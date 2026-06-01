"""최종 패키징 agent를 서비스 graph에 연결하는 adapter입니다.

각 agent state를 모아 API/프론트가 확인 가능한 markdown 패키지 형태로 합칩니다.
DOCX/HTML 저장은 artifact storage가 붙은 뒤 확장합니다.
"""
from __future__ import annotations

from typing import Any

from agents.adapters.base import AgentAdapter
from agents.schemas.composer import ComposerAgentOutput


class ComposerAdapter(AgentAdapter[ComposerAgentOutput]):
    agent_name = "composer"
    state_key = "final_package"
    schema = ComposerAgentOutput

    def build_input(self, state: dict[str, Any]) -> dict[str, Any]:
        return dict(state)

    def call_agent(self, state_input: dict[str, Any]) -> ComposerAgentOutput:
        summary = state_input.get("summary", {}) or {}
        title = summary.get("project_name") or "특허 초안 패키지"
        markdown = (
            f"# {title}\n\n"
            f"## 요약\n{summary.get('readable_summary', '')}\n\n"
            "## 상태\n서비스 골격 패키징 결과입니다."
        )
        return ComposerAgentOutput(
            status="ok",
            summary="최종 패키징 adapter 골격 실행 완료",
            title=title,
            abstract=summary.get("readable_summary", ""),
            sections={"summary": summary.get("readable_summary", "")},
            claims=(state_input.get("claims") or {}).get("draft_claims", []),
            drawings=state_input.get("drawings") or {},
            specification=state_input.get("specification") or {},
            prior_art_report=state_input.get("prior_art") or {},
            rendered_markdown=markdown,
            composer_notes=["DOCX/HTML artifact 저장 로직 연결 필요"],
        )
