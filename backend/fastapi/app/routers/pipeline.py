"""서비스 pipeline API router입니다.

─ 이 파일의 역할 ─
  - POST /api/pipeline/run      : 새 파이프라인 실행
  - POST /api/pipeline/continue : 기존 파이프라인 이어서 실행

─ 저장 흐름 ─
  /run 요청
    1. PostgreSQL에 run 생성 (status=running)
    2. Redis에 "지금 실행 중인 agent" 마킹
    3. 파이프라인 실행 (agent 시작마다 Redis 진행상황 업데이트)
    4. 완료/실패 시 PostgreSQL 최종 업데이트

  GET /api/runs/{run_id}
    - PostgreSQL: 영구 결과 조회
    - Redis: 실시간 현재 agent 조회

─ async/await와 asyncio.to_thread ─
  run_service_pipeline()은 동기 함수입니다. LLM API 호출 동안 블로킹됩니다.
  asyncio.to_thread()로 별도 스레드에서 실행해서 이벤트 루프를 막지 않습니다.

─ 현재 한계 (TODO) ─
  /continue는 아직 클라이언트가 state 전체를 body로 보냅니다.
  /run이 run_id를 즉시 반환하고 worker가 뒤에서 처리하는 queued 방식은 미구현입니다.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import redis as redis_lib
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agents.graph import (
    DEFAULT_PIPELINE,
    build_agent_state_key_map,
    build_default_adapters,
    run_service_pipeline,
)
from agents.master.router import decide_next_agent
from agents.state import create_initial_state
from backend.fastapi.app.db import get_db
from backend.fastapi.app.models import Run

router = APIRouter()

# Redis 클라이언트: from_url()은 실제 연결을 하지 않습니다.
# 첫 번째 명령 실행 시 연결됩니다. Redis 없는 환경에서도 import는 정상입니다.
_redis = redis_lib.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/0"),
    decode_responses=True,
)

# Redis TTL: 실행 진행상황 키를 하루 동안 유지합니다.
_REDIS_TTL = 86400  # 1일 (초)


def _make_progress_callback(run_id: str):
    """agent 시작 시 Redis 진행상황을 업데이트하는 콜백을 만듭니다.

    graph.py의 progress_callback 파라미터로 넘깁니다.
    Redis 장애 시에도 파이프라인이 중단되지 않도록 예외를 내부에서 처리합니다.
    """
    def callback(agent_name: str) -> None:
        try:
            # "run:{run_id}:agent" 키에 현재 실행 중인 agent 이름을 저장
            _redis.setex(f"run:{run_id}:agent", _REDIS_TTL, agent_name)
        except Exception:
            pass  # Redis 실패는 무시
    return callback


def _save_run_start(db: Session, run_id: str, user_input: str) -> Run:
    """파이프라인 시작 시 PostgreSQL에 run 레코드를 생성합니다."""
    db_run = Run(
        run_id=run_id,
        status="running",
        user_input=user_input,
    )
    db.add(db_run)
    db.commit()
    return db_run


def _update_run_end(db: Session, db_run: Run, state: dict[str, Any]) -> None:
    """파이프라인 완료/실패 시 PostgreSQL 레코드를 최종 상태로 업데이트합니다."""
    db_run.status = (state.get("workflow") or {}).get("status", "failed")
    db_run.state = state
    db_run.errors = (state.get("workflow") or {}).get("errors") or []
    db_run.updated_at = datetime.now(timezone.utc)
    db.commit()


class PipelineRunRequest(BaseModel):
    """POST /api/pipeline/run 요청 body 구조입니다."""

    user_input: str = Field(..., min_length=1)
    route: list[str] | None = None


class PipelineContinueRequest(BaseModel):
    """POST /api/pipeline/continue 요청 body 구조입니다.

    TODO: DB 세션 구현 완료 후 state 대신 run_id만 받도록 전환 예정.
    """

    state: dict[str, Any]
    user_input: str | None = None
    route: list[str] | None = None


@router.post("/run")
async def run_pipeline(request: PipelineRunRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """새 run_id를 만들고 파이프라인을 실행합니다.

    실행 중 Redis에 진행상황이 업데이트되고,
    완료/실패 시 PostgreSQL에 최종 결과가 저장됩니다.

    응답 구조:
    {
        "run_id": "uuid",
        "state": { ... },
        "decision": { ... }
    }
    """
    run_id = str(uuid4())
    adapters = build_default_adapters()

    # PostgreSQL에 run 시작 기록
    db_run = _save_run_start(db, run_id, request.user_input)

    # asyncio.to_thread(): 동기 파이프라인을 별도 스레드에서 실행
    # progress_callback으로 각 agent 시작 시 Redis에 진행상황 업데이트
    state = await asyncio.to_thread(
        run_service_pipeline,
        request.user_input,
        adapters,
        route=tuple(request.route or DEFAULT_PIPELINE),
        progress_callback=_make_progress_callback(run_id),
    )

    state.setdefault("run_session", {})
    state["run_session"]["run_id"] = run_id

    # PostgreSQL에 최종 결과 저장
    _update_run_end(db, db_run, state)

    return {"run_id": run_id, "state": state, "decision": state.get("master_decision", {})}


@router.post("/continue")
async def continue_pipeline(
    request: PipelineContinueRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """추가 사용자 입력을 반영한 뒤 다음 단계만 실행합니다."""
    state = request.state or create_initial_state(request.user_input or "")
    if request.user_input:
        previous = str(state.get("user_input") or "")
        state["user_input"] = f"{previous}\n{request.user_input}".strip()

    adapters = build_default_adapters()
    agent_state_keys = build_agent_state_key_map(adapters)
    decision = decide_next_agent(state, request.route, agent_state_keys=agent_state_keys)

    if decision.next_agent == "end" or decision.requires_user_input:
        return {"state": state, "decision": decision.model_dump(mode="json")}

    run_id = (state.get("run_session") or {}).get("run_id") or str(uuid4())

    next_state = await asyncio.to_thread(
        run_service_pipeline,
        state.get("user_input", ""),
        adapters,
        initial_state=state,
        route=tuple(request.route or decision.route or [decision.next_agent]),
        progress_callback=_make_progress_callback(run_id),
    )

    # run_id가 DB에 있으면 최종 상태 업데이트
    db_run = db.query(Run).filter(Run.run_id == run_id).first()
    if db_run is not None:
        _update_run_end(db, db_run, next_state)

    return {"state": next_state, "decision": next_state.get("master_decision", {})}
