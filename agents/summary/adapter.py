"""요약본작성 agent를 서비스 graph에 연결하는 adapter입니다.

현재는 서비스 골격 검증을 위해 입력 문자열을 구조화 요약 형태로 감싸는 안전한 기본 구현을 둡니다.
실제 LLM 기반 요약 로직은 이 adapter의 `call_agent` 내부에서 교체하면 됩니다.
"""
from __future__ import annotations

from typing import Any

from agents.adapters.base import AgentAdapter
from agents.schemas.summary import SummaryAgentOutput, StructuredInvention


class SummaryAdapter(AgentAdapter[SummaryAgentOutput]):
    agent_name = "summary"
    state_key = "summary"
    schema = SummaryAgentOutput

    def build_input(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"user_input": state.get("user_input", ""), "summary": state.get("summary", {})}

    def call_agent(self, state_input: dict[str, Any]) -> SummaryAgentOutput:
        user_input = str(state_input.get("user_input") or "").strip()
        missing = [] if len(user_input) >= 30 else ["발명의 문제/해결수단/효과를 더 구체화해야 합니다."]
        return SummaryAgentOutput(
            status="needs_user_input" if missing else "ok",
            summary="사용자 입력을 서비스 state용 요약으로 정리했습니다.",
            project_name="발명 명칭 미정",
            problem_to_solve=user_input,
            core_technology=user_input,
            expected_effect="입력 기반 효과 확인 필요",
            readable_summary=user_input,
            structured_invention=StructuredInvention(
                title="발명 명칭 미정",
                problem=user_input,
                solution=user_input,
                expected_effects=["입력 기반 효과 확인 필요"],
                missing_slots=missing,
                clarification_questions=missing,
            ),
            warnings=missing,
        )
