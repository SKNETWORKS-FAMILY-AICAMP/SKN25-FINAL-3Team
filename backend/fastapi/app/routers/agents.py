"""[DEPRECATED] 개별 agent 단독 실행 API router입니다.

⚠️  이 라우터는 deprecated 상태입니다.
    전체 state를 body로 전달하는 방식 대신,
    run_id 기반으로 DB에서 state를 로드하는 새 엔드포인트를 사용하세요.

    신규: POST /api/runs/{run_id}/agents/{agent_name}/run
    구버전: POST /api/agents/{agent_name}/run  ← 이 파일

    구버전은 하위 호환성을 위해 유지하지만 향후 제거될 예정입니다.
    내부 디버깅·테스트 전용으로만 사용하세요.
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.graph import get_default_adapters
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
    adapters = get_default_adapters()
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
