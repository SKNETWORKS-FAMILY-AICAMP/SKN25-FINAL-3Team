"""개별 agent 단독 실행 API router입니다.

─ 이 파일의 역할 ─
  복잡한 분기 그래프 구조에서 각 agent 노드를 개별로 호출할 때 씁니다.
  pipeline router와 달리 전체 파이프라인이 아니라 지정한 agent 하나만 실행합니다.

  POST /api/agents/{agent_name}/run

─ 언제 쓰나? ─
  - 특정 agent만 재실행하고 싶을 때 (예: claim만 다시 돌리기)
  - 파이프라인이 특정 agent에서 실패(AgentValidationError)했을 때 해당 agent만 재시도
  - 복잡한 분기 그래프에서 노드별로 순서를 직접 제어할 때
  - 디버깅/테스트 목적으로 특정 agent만 격리해서 실행할 때

─ pipeline/run과의 차이 ─
  /pipeline/run → 여러 agent를 순서대로 전부 실행
  /agents/{name}/run → 지정한 agent 하나만 실행
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.graph import build_default_adapters
from agents.validation import AgentValidationError

router = APIRouter()


class AgentRunRequest(BaseModel):
    """POST /api/agents/{agent_name}/run 요청 body 구조입니다.

    state: 현재 전체 PatentAgentState를 넘겨야 합니다.
           agent는 state에서 필요한 입력을 직접 뽑아 씁니다.
           예: claim agent는 state["summary"]를 읽어서 청구항을 만듭니다.
    """

    state: dict[str, Any]


@router.post("/{agent_name}/run")
async def run_single_agent(agent_name: str, request: AgentRunRequest) -> dict[str, Any]:
    """지정된 agent 하나만 실행하고 업데이트된 state와 agent output을 반환합니다.

    사용 가능한 agent 이름은 build_default_adapters()에 등록된 것과 동일합니다.
    현재: summary, prior_art, claim, drawing, specification, composer

    Args:
        agent_name: URL 경로 파라미터. 예: /api/agents/summary/run → agent_name = "summary"
        request: state를 담은 요청 body

    Returns:
        {
            "state": { ... },           # agent output이 추가된 전체 state
            "agent_output": { ... }     # 이번에 실행된 agent의 결과만
        }

    Raises:
        HTTPException 404: agent_name이 존재하지 않을 때
    """
    # build_default_adapters()가 adapter 등록 단일 기준입니다.
    # 별도 유효성 목록(_VALID_AGENTS)을 따로 관리하지 않습니다.
    # 새 agent를 추가하면 여기 자동으로 반영됩니다.
    adapters = build_default_adapters()
    adapter = adapters.get(agent_name)

    if adapter is None:
        raise HTTPException(
            status_code=404,
            detail=f"unknown agent: {agent_name!r}. available: {sorted(adapters)}",
        )

    state = dict(request.state)  # 원본 state를 수정하지 않도록 복사

    # adapter.run()을 asyncio.to_thread()로 실행 (동기 함수이므로 별도 스레드에서)
    try:
        agent_output = await asyncio.to_thread(adapter.run, state)
    except AgentValidationError as exc:
        # agent output이 schema 검증을 통과하지 못한 경우입니다.
        # 서버 코드 오류(500)가 아니라, 입력/agent output 형식 문제이므로 422로 반환합니다.
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

    # adapter.state_key: 이 agent의 결과를 저장할 state key
    # 예: claim adapter는 state_key = "claims"이므로 state["claims"]에 저장됩니다.
    state[adapter.state_key] = agent_output

    return {"state": state, "agent_output": agent_output}
