"""서비스 pipeline API router입니다.

외부 클라이언트는 이 API만 호출하고, API는 Master Router와 Graph를 통해
현재 state 기준 다음 단계 실행/사용자 대기/완료 여부를 반환합니다.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.graph import DEFAULT_PIPELINE, build_default_adapters, run_service_pipeline
from agents.master.router import decide_next_agent
from agents.state import create_initial_state

router = APIRouter()


class PipelineRunRequest(BaseModel):
    """새 pipeline 실행 요청입니다."""

    user_input: str = Field(..., min_length=1)
    route: list[str] | None = None


class PipelineContinueRequest(BaseModel):
    """기존 state를 이어서 실행하는 요청입니다."""

    state: dict[str, Any]
    user_input: str | None = None
    route: list[str] | None = None


@router.post("/run")
def run_pipeline(request: PipelineRunRequest) -> dict[str, Any]:
    """새 run_id를 만들고 요청 route 또는 기본 service pipeline을 실행합니다."""
    run_id = str(uuid4())
    state = run_service_pipeline(
        request.user_input,
        build_default_adapters(),
        route=tuple(request.route or DEFAULT_PIPELINE),
    )
    state.setdefault("run_session", {})
    state["run_session"]["run_id"] = run_id
    decision = decide_next_agent(state, request.route)
    return {"run_id": run_id, "state": state, "decision": decision.model_dump(mode="json")}


@router.post("/continue")
def continue_pipeline(request: PipelineContinueRequest) -> dict[str, Any]:
    """추가 사용자 입력을 반영한 뒤 Master 판단에 따라 다음 단계만 실행합니다."""
    state = request.state or create_initial_state(request.user_input or "")
    if request.user_input:
        previous = str(state.get("user_input") or "")
        state["user_input"] = f"{previous}\n{request.user_input}".strip()

    decision = decide_next_agent(state, request.route)
    if decision.next_agent == "end" or decision.requires_user_input:
        return {"state": state, "decision": decision.model_dump(mode="json")}

    next_state = run_service_pipeline(
        state.get("user_input", ""),
        build_default_adapters(),
        initial_state=state,
        route=tuple(request.route or decision.route or [decision.next_agent]),
    )
    return {"state": next_state, "decision": decide_next_agent(next_state, request.route).model_dump(mode="json")}
