"""명세서 agent를 서비스 graph에 연결하는 adapter입니다.

요약, 선행기술, 청구항, 도면 state를 받아 명세서 섹션 형태로 정규화합니다.
실제 명세서 작성 LLM은 이 adapter의 `call_agent`에서 연결합니다.
"""
from __future__ import annotations

from typing import Any

from agents.adapters.base import AgentAdapter
from agents.schemas.specification import SpecificationAgentOutput


class SpecificationAdapter(AgentAdapter[SpecificationAgentOutput]):
    agent_name = "specification"
    state_key = "specification"
    schema = SpecificationAgentOutput

    def build_input(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": state.get("summary", {}) or {},
            "prior_art": state.get("prior_art", {}) or {},
            "claims": state.get("claims", {}) or {},
            "drawings": state.get("drawings", {}) or {},
        }

    def call_agent(self, state_input: dict[str, Any]) -> SpecificationAgentOutput:
        summary = state_input.get("summary") or {}
        structured = summary.get("structured_invention", {}) or {}
        return SpecificationAgentOutput(
            status="ok",
            summary="명세서 adapter 골격 실행 완료",
            technical_field=structured.get("technical_field_natural", "AI/소프트웨어 특허 기술분야"),
            background_art=structured.get("prior_art_problem", "기존 기술의 문제점 확인 필요"),
            problem_to_solve=structured.get("problem", "해결 과제 확인 필요"),
            means_for_solving=structured.get("solution", "해결 수단 확인 필요"),
            effects="; ".join(structured.get("expected_effects", [])) or "발명의 효과 확인 필요",
            brief_description_of_drawings="도 1은 시스템 구성도이고, 도 2는 방법 흐름도입니다.",
            detailed_description=summary.get("readable_summary", "상세한 설명 생성 로직 연결 필요"),
        )
