"""중간발표 MVP용 단방향 graph skeleton.

실제 LangGraph(StateGraph) 연결 전에도 같은 계약을 테스트할 수 있도록 단순 순차 실행기로 둔다.
각 node는 PatentAgentState를 입력으로 받고, raw output을 반환한다.
Master/Graph는 raw output을 Pydantic 검증/repair/fallback 후 state에 병합한다.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agents.schemas import (
    ClaimAgentOutput,
    ComposerAgentOutput,
    ConsultationAgentOutput,
    DrawingAgentOutput,
    PriorArtAgentOutput,
    SpecificationAgentOutput,
)
from agents.state import PatentAgentState, create_initial_state
from agents.validation import safe_validate_output

AgentRunner = Callable[[PatentAgentState], Any]


def _fallbacks() -> dict[str, Any]:
    return {
        "consultation": ConsultationAgentOutput(status="failed", summary="상담 agent output 검증 실패"),
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
    "consultation": ConsultationAgentOutput,
    "claim": ClaimAgentOutput,
    "drawing": DrawingAgentOutput,
    "prior_art": PriorArtAgentOutput,
    "specification": SpecificationAgentOutput,
    "composer": ComposerAgentOutput,
}

STATE_KEYS = {
    "consultation": "consultation",
    "claim": "claims",
    "drawing": "drawings",
    "prior_art": "prior_art",
    "specification": "specification",
    "composer": "final_package",
}

DEFAULT_PIPELINE = ("consultation", "claim", "drawing", "prior_art", "specification", "composer")


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
        validated = safe_validate_output(
            agent_name=agent_name,
            schema=SCHEMAS[agent_name],
            raw_output=raw_output,
            fallback=fallbacks[agent_name],
            enable_llm_repair=enable_llm_repair,
        )
        state_key = STATE_KEYS[agent_name]
        state[state_key] = validated.model_dump()  # type: ignore[literal-required]

    state["workflow"]["status"] = "completed"
    state["workflow"]["current_agent"] = "master"
    state["workflow"]["next_agent"] = "review"
    return state
