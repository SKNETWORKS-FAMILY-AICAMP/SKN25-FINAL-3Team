"""파이프라인 실행 조회 및 agent 재실행 API router입니다.

GET  /api/runs/{run_id}
  - PostgreSQL에서 영구 저장된 run 정보를 조회합니다.
  - Redis에서 실시간 현재 진행 중인 agent를 조회합니다.

POST /api/runs/{run_id}/agents/{agent_name}/run
  - DB에서 state를 읽어 특정 agent만 재실행합니다.
  - 결과를 DB에 저장하고 반환합니다.

─ PostgreSQL vs Redis 역할 분리 ─
  PostgreSQL: 영구 저장 (완료/실패 후 상태, 전체 결과)
  Redis      : 실시간 현황 (지금 어떤 agent가 돌고 있는지)

  파이프라인이 실행 중이면 Redis만 업데이트되고 있습니다.
  파이프라인이 완료/실패하면 PostgreSQL도 최종 상태로 업데이트됩니다.

─ TODO (미구현 엔드포인트) ─
  POST /api/runs/{run_id}/continue
    현재 /api/pipeline/continue 가 state 전체를 body로 받는 방식.
    run_id만 받아 DB에서 state를 로드하는 방식으로 전환 예정.

  GET  /api/runs/{run_id}/steps
    step별 실행 기록 (run_steps 테이블 구현 후)

  GET  /api/runs/{run_id}/artifacts
    생성된 DOCX/HTML/SVG artifact 목록 (Object Storage 연동 후)
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.graph import get_default_adapters
from agents.validation import AgentValidationError
from backend.fastapi.app.db import get_db, redis_client as _redis
from backend.fastapi.app.models import Run

router = APIRouter()


class AgentRerunRequest(BaseModel):
    """POST /api/runs/{run_id}/agents/{agent_name}/run 요청 body입니다.

    overrides: 실행 전 state에 덮어쓸 key-value (선택적).
               특정 입력값만 바꿔서 agent를 재실행할 때 사용합니다.
               예: {"user_input": "수정된 발명 설명"}
    """

    overrides: dict[str, Any] | None = None


@router.get("/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)) -> dict:
    """run_id로 파이프라인 실행 상태와 결과를 조회합니다.

    응답에 포함되는 정보:
    - run_id, status, user_input: 기본 정보
    - current_agent: 지금 실행 중인 agent (Redis, 실시간)
    - completed_agents: 완료된 agent 목록 (state.workflow.trace에서 추출)
    - errors: 에러 목록
    - master_decision: 다음 단계 판단 결과
    - created_at / updated_at: 시각 정보

    Redis에서 current_agent를 읽을 수 없으면 (Redis 없거나 만료)
    PostgreSQL의 state에서 마지막으로 알려진 agent를 씁니다.
    """
    # PostgreSQL에서 run 조회
    run = db.query(Run).filter(Run.run_id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"run not found: {run_id!r}")

    # Redis에서 실시간 현재 agent 조회
    # 파이프라인이 실행 중이면 여기에 최신 agent 이름이 있습니다.
    current_agent: str | None = None
    try:
        current_agent = _redis.get(f"run:{run_id}:agent")
    except Exception:
        pass  # Redis 없어도 나머지 정보는 정상 반환

    # state에서 완료된 agent 목록 추출
    state = run.state or {}
    workflow = state.get("workflow", {})
    trace: list[dict] = workflow.get("trace", [])
    completed_agents = [t["agent"] for t in trace if isinstance(t, dict) and "agent" in t]

    # Redis에 current_agent가 없거나 run이 끝났으면 DB의 current_agent를 사용
    if current_agent is None or run.status != "running":
        current_agent = workflow.get("current_agent")

    return {
        "run_id": run.run_id,
        "status": run.status,
        "user_input": run.user_input,
        "current_agent": current_agent,        # 지금 실행 중인 agent (실시간)
        "completed_agents": completed_agents,  # 완료된 agent 목록
        "errors": run.errors or [],
        "master_decision": state.get("master_decision"),
        "state": state,                        # 전체 파이프라인 결과 상태
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }


@router.post("/{run_id}/agents/{agent_name}/run")
async def rerun_agent(
    run_id: str,
    agent_name: str,
    request: AgentRerunRequest | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """DB에서 state를 읽어 특정 agent만 재실행합니다.

    파이프라인 실패 후 특정 agent만 재시도하거나,
    청구항·명세서 등 특정 결과물만 다시 생성할 때 사용합니다.

    동작 순서:
    1. PostgreSQL에서 run과 저장된 state를 로드합니다.
    2. request.overrides가 있으면 state에 덮어씁니다.
    3. 지정한 agent를 실행합니다.
    4. 성공 시 state를 DB에 저장하고, 이 agent 관련 에러를 제거합니다.

    Args:
        run_id: 재실행할 파이프라인의 run ID
        agent_name: 실행할 agent 이름 (summary, prior_art, claim, drawing, specification, composer)
        request: 선택적 state 오버라이드

    Returns:
        {
            "run_id": "...",
            "agent": "claim",
            "agent_output": { ... },  # 이번에 실행된 agent의 결과
            "state": { ... }          # 업데이트된 전체 state
        }

    Raises:
        HTTPException 404: run_id 또는 agent_name이 존재하지 않을 때
        HTTPException 422: agent output이 schema 검증을 통과하지 못할 때
    """
    run = db.query(Run).filter(Run.run_id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail=f"run not found: {run_id!r}")

    adapters = get_default_adapters()
    adapter = adapters.get(agent_name)
    if adapter is None:
        raise HTTPException(
            status_code=404,
            detail=f"unknown agent: {agent_name!r}. available: {sorted(adapters)}",
        )

    state = dict(run.state or {})
    if request and request.overrides:
        state.update(request.overrides)

    try:
        agent_output = await asyncio.to_thread(adapter.run, state)
    except AgentValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "agent_name": exc.agent_name,
                "schema_name": exc.schema_name,
                "validation_errors": exc.validation_errors,
                "repair_error": exc.repair_error,
                "message": "agent output이 schema 검증을 통과하지 못했습니다.",
            },
        ) from exc

    # state에 agent 결과 반영
    state[adapter.state_key] = agent_output

    # 이 agent와 관련된 에러만 제거 (재실행 성공 처리)
    run.errors = [e for e in (run.errors or []) if agent_name not in e]
    run.state = state
    run.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "run_id": run_id,
        "agent": agent_name,
        "agent_output": agent_output,
        "state": state,
    }
