"""서비스 pipeline API router입니다.

─ 이 파일의 역할 ─
  외부 클라이언트(프론트엔드 또는 다른 서비스)가 호출하는 API endpoint 2개를 정의합니다.
  - POST /api/pipeline/run      : 새 파이프라인 실행
  - POST /api/pipeline/continue : 기존 파이프라인 이어서 실행

─ async/await와 asyncio.to_thread ─
  FastAPI는 비동기(async) 서버입니다. 요청이 오면 이벤트 루프에서 처리합니다.
  문제: run_service_pipeline()은 동기 함수입니다. LLM API를 호출하는 동안 멈춥니다.
  동기 함수를 async 함수 안에서 직접 호출하면 그 시간 동안 서버 전체가 멈춥니다.

  해결: asyncio.to_thread()
  동기 함수를 별도 스레드에서 실행합니다.
  LLM이 응답하는 동안 이벤트 루프는 다른 요청을 처리할 수 있습니다.

  주의: 이것은 "백그라운드 큐"가 아닙니다.
  /run 요청은 여전히 agent 실행이 끝날 때까지 기다린 뒤 응답합니다.
  운영형 구조에서는 /run이 run_id만 즉시 반환하고 worker가 뒤에서 실행해야 합니다.

─ 현재 한계 (TODO) ─
  /continue 엔드포인트는 클라이언트가 state 전체를 요청 body로 보냅니다.
  DB 세션 구현 후 run_id만 받도록 전환 예정입니다.
"""
from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.graph import (
    DEFAULT_PIPELINE,
    build_agent_state_key_map,
    build_default_adapters,
    run_service_pipeline,
)
from agents.master.router import decide_next_agent
from agents.state import create_initial_state

# APIRouter: 이 파일의 endpoint들을 그룹으로 묶는 객체입니다.
# main.py에서 app.include_router(router, prefix="/api/pipeline")으로 등록됩니다.
router = APIRouter()


class PipelineRunRequest(BaseModel):
    """POST /api/pipeline/run 요청 body 구조입니다.

    Pydantic BaseModel을 상속하면 요청이 오자마자 타입 검증이 자동으로 됩니다.
    user_input이 빈 문자열이면 min_length=1 덕분에 422 에러가 납니다.
    """

    user_input: str = Field(..., min_length=1)  # 사용자가 입력한 발명 설명 (필수)
    route: list[str] | None = None  # 실행할 agent 순서. None이면 DEFAULT_PIPELINE 전체 실행.


class PipelineContinueRequest(BaseModel):
    """POST /api/pipeline/continue 요청 body 구조입니다.

    TODO: DB 세션 구현 후 state 대신 run_id만 받도록 전환 예정.
          지금은 클라이언트가 이전 응답의 state를 그대로 다시 보내줍니다.
    """

    state: dict[str, Any]           # 이전 /run 또는 /continue 응답의 state
    user_input: str | None = None   # 사용자 추가 입력 (마스터가 질문을 했을 때)
    route: list[str] | None = None  # 실행할 agent 순서 지정 (선택)


@router.post("/run")
async def run_pipeline(request: PipelineRunRequest) -> dict[str, Any]:
    """새 run_id를 만들고 요청 route 또는 기본 service pipeline을 실행합니다.

    현재 구현은 asyncio.to_thread로 서버 이벤트 루프 차단만 줄인 동기형 실행입니다.
    즉 /run은 아직 백그라운드 큐가 아니며, pipeline 실행이 끝난 뒤 응답합니다.
    DB/Redis worker가 붙으면 run_id를 즉시 반환하는 queued 방식으로 바꿉니다.

    응답 구조:
    {
        "run_id": "uuid",          # 이번 실행의 고유 ID
        "state": { ... },           # 전체 PatentAgentState
        "decision": { ... }         # master_decision (다음 단계 정보)
    }
    """
    run_id = str(uuid4())  # uuid4(): 충돌 확률이 거의 0인 랜덤 고유 ID 생성

    adapters = build_default_adapters()

    # asyncio.to_thread(): 동기 함수(run_service_pipeline)를 별도 스레드에서 실행합니다.
    # await를 붙이면 스레드가 완료될 때까지 이 코루틴이 기다립니다.
    # 기다리는 동안 이벤트 루프는 다른 요청을 처리할 수 있습니다.
    state = await asyncio.to_thread(
        run_service_pipeline,
        request.user_input,
        adapters,
        route=tuple(request.route or DEFAULT_PIPELINE),
    )

    # run_session에 run_id 저장 (DB 연결 전 임시)
    state.setdefault("run_session", {})
    state["run_session"]["run_id"] = run_id

    # run_service_pipeline이 이미 master_decision을 state에 저장했으므로 그대로 사용
    return {"run_id": run_id, "state": state, "decision": state.get("master_decision", {})}


@router.post("/continue")
async def continue_pipeline(request: PipelineContinueRequest) -> dict[str, Any]:
    """추가 사용자 입력을 반영한 뒤 Master 판단에 따라 다음 단계만 실행합니다.

    흐름:
    1. 사용자 입력이 있으면 기존 user_input에 이어 붙임
    2. decide_next_agent()로 현재 state에서 다음 할 일 판단
    3. "끝났거나 또 사용자 입력이 필요"하면 그냥 반환
    4. 아니면 다음 agent 실행 후 반환

    응답 구조:
    {
        "state": { ... },     # 업데이트된 전체 PatentAgentState
        "decision": { ... }   # master_decision (다음 단계 정보)
    }
    """
    # state가 없으면 새로 만들어서 시작 (방어 코드)
    state = request.state or create_initial_state(request.user_input or "")

    # 사용자 추가 입력을 기존 입력에 이어 붙임
    if request.user_input:
        previous = str(state.get("user_input") or "")
        state["user_input"] = f"{previous}\n{request.user_input}".strip()

    # 현재 state에서 다음 할 일을 판단
    adapters = build_default_adapters()
    agent_state_keys = build_agent_state_key_map(adapters)
    decision = decide_next_agent(state, request.route, agent_state_keys=agent_state_keys)

    # 이미 완료됐거나 또 사용자 입력이 필요하면 실행 없이 반환
    if decision.next_agent == "end" or decision.requires_user_input:
        return {"state": state, "decision": decision.model_dump(mode="json")}

    # 다음 agent 실행 (asyncio.to_thread로 별도 스레드에서)
    next_state = await asyncio.to_thread(
        run_service_pipeline,
        state.get("user_input", ""),
        adapters,
        initial_state=state,
        route=tuple(request.route or decision.route or [decision.next_agent]),
    )
    return {"state": next_state, "decision": next_state.get("master_decision", {})}
