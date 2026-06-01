"""선행기술조사 agent를 서비스 graph에 연결하는 adapter입니다.

서비스 골격에서는 외부 DB/검색 의존성 없이 query와 평가 기준 자리만 state에 남깁니다.
실제 검색 구현은 `agents/priorart/prior_art_agent.py` 호출로 교체하면 됩니다.
"""
from __future__ import annotations

from typing import Any

from agents.adapters.base import AgentAdapter
from agents.schemas.prior_art import PriorArtAgentOutput


class PriorArtAdapter(AgentAdapter[PriorArtAgentOutput]):
    agent_name = "prior_art"
    state_key = "prior_art"
    schema = PriorArtAgentOutput
    fallback = PriorArtAgentOutput(status="failed", summary="prior_art output validation failed")

    def build_input(self, state: dict[str, Any]) -> dict[str, Any]:
        summary = state.get("summary", {}) or {}
        structured = summary.get("structured_invention", {}) or {}
        query = " ".join(
            str(x)
            for x in [structured.get("problem", ""), structured.get("solution", ""), summary.get("readable_summary", "")]
            if x
        )
        return {"query": query, "summary": summary, "structured_invention": structured}

    def call_agent(self, state_input: dict[str, Any]) -> PriorArtAgentOutput:
        query = str(state_input.get("query") or "").strip()
        return PriorArtAgentOutput(
            status="ok",
            summary="선행기술 검색 adapter 골격 실행 완료",
            query=query,
            ipc_focus=["G06F", "G06N", "G06Q", "G06V"],
            analysis_summary="실제 검색 엔진 연결 전이므로 후보는 비워둡니다.",
            limitations=["검색 DB/임베딩 연결 필요"],
        )
