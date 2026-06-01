"""서비스용 agent graph 실행 골격입니다.

중간발표용 고정 단방향 데모가 아니라, Master Router가 정한 route만 실행하고
각 단계는 adapter를 통해 schema 검증 후 shared state에 병합합니다.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from agents.adapters.base import AgentAdapter
from agents.claim.adapter import ClaimAdapter
from agents.composer.adapter import ComposerAdapter
from agents.drawing.adapter import DrawingAdapter
from agents.master.router import SERVICE_PIPELINE, decide_next_agent
from agents.priorart.adapter import PriorArtAdapter
from agents.specification.adapter import SpecificationAdapter
from agents.state import PatentAgentState, create_initial_state
from agents.summary.adapter import SummaryAdapter

DEFAULT_PIPELINE = SERVICE_PIPELINE


def build_default_adapters() -> dict[str, AgentAdapter[Any]]:
    """서비스 graph가 기본으로 사용할 adapter 목록을 만듭니다."""
    adapters: list[AgentAdapter[Any]] = [
        SummaryAdapter(),
        PriorArtAdapter(),
        ClaimAdapter(),
        DrawingAdapter(),
        SpecificationAdapter(),
        ComposerAdapter(),
    ]
    return {adapter.agent_name: adapter for adapter in adapters}


def run_service_pipeline(
    user_input: str,
    adapters: dict[str, AgentAdapter[Any]] | None = None,
    *,
    initial_state: PatentAgentState | None = None,
    route: Sequence[str] | None = None,
    enable_llm_repair: bool | None = None,
) -> PatentAgentState:
    """주어진 route만 실행하고 결과를 state에 병합합니다."""
    state = initial_state or create_initial_state(user_input)
    state["user_input"] = user_input or state.get("user_input", "")
    state.setdefault("workflow", {})
    state["workflow"]["status"] = "running"
    state["workflow"].setdefault("errors", [])
    state["workflow"].setdefault("trace", [])

    adapter_map = adapters or build_default_adapters()
    selected_route = tuple(route or DEFAULT_PIPELINE)

    for agent_name in selected_route:
        adapter = adapter_map.get(agent_name)
        state["workflow"]["current_agent"] = agent_name  # type: ignore[typeddict-item]
        if adapter is None:
            state["workflow"]["errors"].append(f"adapter not registered: {agent_name}")
            continue
        try:
            state[adapter.state_key] = adapter.run(state, enable_llm_repair=enable_llm_repair)  # type: ignore[literal-required]
            state["workflow"]["trace"].append({"agent": agent_name, "action": "run", "summary": "adapter executed"})
        except Exception as exc:  # 서비스 골격에서는 실패 위치를 state에 남기고 중단합니다.
            state["workflow"]["status"] = "failed"
            state["workflow"]["errors"].append(f"{agent_name}: {type(exc).__name__}: {exc}")
            return state

        decision = decide_next_agent(state)
        if decision.requires_user_input:
            state["workflow"]["status"] = "wait_user"
            state["workflow"]["next_agent"] = "master"
            state["master_decision"] = decision.model_dump(mode="json")
            return state

    final_decision = decide_next_agent(state)
    state["workflow"]["status"] = "completed" if final_decision.status == "completed" else "running"
    state["workflow"]["current_agent"] = "master"
    state["workflow"]["next_agent"] = final_decision.next_agent if final_decision.next_agent != "end" else "review"
    state["master_decision"] = final_decision.model_dump(mode="json")
    return state


def run_mvp_pipeline(user_input: str, runners: dict[str, Any] | None = None, **_: Any) -> PatentAgentState:
    """이전 호출부 호환용 wrapper입니다. 신규 코드는 run_service_pipeline을 사용합니다."""
    return run_service_pipeline(user_input, build_default_adapters())
