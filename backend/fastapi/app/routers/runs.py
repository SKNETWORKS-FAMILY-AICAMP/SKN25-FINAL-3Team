"""파이프라인 실행 조회 API router입니다.

GET /api/runs/{run_id}
  - PostgreSQL에서 영구 저장된 run 정보를 조회합니다.
  - Redis에서 실시간 현재 진행 중인 agent를 조회합니다.

─ PostgreSQL vs Redis 역할 분리 ─
  PostgreSQL: 영구 저장 (완료/실패 후 상태, 전체 결과)
  Redis      : 실시간 현황 (지금 어떤 agent가 돌고 있는지)

  파이프라인이 실행 중이면 Redis만 업데이트되고 있습니다.
  파이프라인이 완료/실패하면 PostgreSQL도 최종 상태로 업데이트됩니다.
"""
from __future__ import annotations

import os

import redis as redis_lib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.fastapi.app.db import get_db
from backend.fastapi.app.models import Run

router = APIRouter()

# Redis 클라이언트: from_url()은 실제로 연결하지 않습니다.
# 첫 번째 명령을 실행할 때 연결됩니다.
_redis = redis_lib.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/0"),
    decode_responses=True,  # bytes 대신 str로 반환
)


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
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }
