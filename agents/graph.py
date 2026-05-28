"""중간발표 MVP용 단방향 graph skeleton.

실제 LangGraph(StateGraph) 연결 전에도 같은 계약을 테스트할 수 있도록 단순 순차 실행기로 둔다.
각 node는 PatentAgentState를 입력으로 받고, raw output을 반환한다.
Master/Graph는 raw output을 Pydantic 검증/repair/fallback 후 state에 병합한다.
Master는 중간발표 MVP에서 지능형 라우터가 아니라 고정 DEFAULT_PIPELINE 실행 관리자다.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any, Protocol

from agents.schemas import (
    ClaimAgentOutput,
    ComposerAgentOutput,
    MasterAgentOutput,
    SummaryAgentOutput,
    DrawingAgentOutput,
    PriorArtAgentOutput,
    SpecificationAgentOutput,
)
from agents.state import PatentAgentState, create_initial_state
from agents.validation import safe_validate_output

AgentRunner = Callable[[PatentAgentState], Any]


class ServiceAdapter(Protocol):
    """graph.py가 의존하는 최소 adapter protocol.

    실제 agent.py 구현은 이 protocol 뒤에 숨긴다. graph는 agent 함수/API를 직접 알지 않는다.
    """

    agent_name: str
    state_key: str

    def run(self, state: PatentAgentState) -> dict[str, Any]: ...


def _trace_event(agent_name: str, state_key: str, output: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent": agent_name,
        "node": f"{agent_name}_adapter",
        "action": "run_adapter",
        "summary": str(output.get("summary") or output.get("status") or "adapter completed")[:240],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "outputs": {"state_key": state_key, "status": output.get("status")},
    }


def _fallbacks() -> dict[str, Any]:
    return {
        "master": MasterAgentOutput(status="failed", summary="Master agent output 검증 실패", stage="failed", action="fail"),
        "summary": SummaryAgentOutput(status="failed", summary="요약본작성 agent output 검증 실패"),
        "claim": ClaimAgentOutput(status="failed", summary="청구항 agent output 검증 실패"),
        "drawing": DrawingAgentOutput(status="failed", summary="도면 agent output 검증 실패"),
        "prior_art": PriorArtAgentOutput(status="failed", summary="선행기술 agent output 검증 실패"),
        "specification": SpecificationAgentOutput(status="failed", summary="발명의 설명 agent output 검증 실패"),
        "composer": ComposerAgentOutput(
            status="failed",
            title="특허 초안 생성 실패",
            abstract="일부 agent output 검증에 실패했습니다.",
            rendered_markdown="# 특허 초안 생성 실패\n\n중간 결과의 warnings/details를 확인하세요.",
            unresolved_items=["agent output validation failed"],
        ),
    }

SCHEMAS = {
    "master": MasterAgentOutput,
    "summary": SummaryAgentOutput,
    "claim": ClaimAgentOutput,
    "drawing": DrawingAgentOutput,
    "prior_art": PriorArtAgentOutput,
    "specification": SpecificationAgentOutput,
    "composer": ComposerAgentOutput,
}

STATE_KEYS = {
    "summary": "summary",
    "claim": "claims",
    "drawing": "drawings",
    "prior_art": "prior_art",
    "specification": "specification",
    "composer": "final_package",
}

DEFAULT_PIPELINE = ("summary", "prior_art", "claim", "drawing", "specification", "composer")


def run_mvp_pipeline(
    user_input: str,
    runners: dict[str, AgentRunner],
    *,
    enable_llm_repair: bool | None = None,
) -> PatentAgentState:
    """등록된 runner를 단방향으로 실행한다.

    아직 구현되지 않은 agent는 건너뛰고 workflow.errors에 남긴다.
    """

    state = create_initial_state(user_input)
    state["workflow"]["status"] = "running"
    fallbacks = _fallbacks()

    for agent_name in DEFAULT_PIPELINE:
        runner = runners.get(agent_name)
        state["workflow"]["current_agent"] = agent_name  # type: ignore[typeddict-item]
        if runner is None:
            state["workflow"]["errors"].append(f"runner not registered: {agent_name}")
            continue

        raw_output = runner(state)
        state_key = STATE_KEYS[agent_name]

        validated = safe_validate_output(
            agent_name=agent_name,
            schema=SCHEMAS[agent_name],
            raw_output=raw_output,
            fallback=fallbacks[agent_name],
            enable_llm_repair=enable_llm_repair,
        )
        state[state_key] = validated.model_dump()  # type: ignore[literal-required]

    state["workflow"]["status"] = "completed"
    state["workflow"]["current_agent"] = "master"
    state["workflow"]["next_agent"] = "review"
    return state


def run_service_pipeline(
    user_input: str,
    adapters: dict[str, ServiceAdapter],
    *,
    route: Sequence[str] = DEFAULT_PIPELINE,
) -> PatentAgentState:
    """서비스 기준 graph 실행기.

    graph.py는 agent.py를 직접 호출하지 않고 adapter만 실행한다.
    adapter는 입력 변환, agent 실행, Pydantic 검증, state 저장용 normalize를 책임진다.
    """

    state = create_initial_state(user_input)
    state["workflow"]["status"] = "running"

    for agent_name in route:
        adapter = adapters.get(agent_name)
        state["workflow"]["current_agent"] = agent_name  # type: ignore[typeddict-item]
        if adapter is None:
            state["workflow"]["errors"].append(f"adapter not registered: {agent_name}")
            continue

        output = adapter.run(state)
        state_key = getattr(adapter, "state_key", STATE_KEYS.get(agent_name, agent_name))
        state[state_key] = output  # type: ignore[literal-required]
        state["workflow"]["trace"].append(_trace_event(agent_name, state_key, output))

    state["workflow"]["status"] = "completed"
    state["workflow"]["current_agent"] = "master"
    state["workflow"]["next_agent"] = "review"
    return state
