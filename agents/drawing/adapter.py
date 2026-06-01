"""도면 agent를 서비스 graph에 연결하는 adapter입니다.

서비스 골격에서는 청구항/요약 state를 기반으로 필요한 도면 후보만 생성합니다.
실제 SVG/이미지 생성기는 이후 이 adapter 뒤에 연결합니다.
"""
from __future__ import annotations

from typing import Any

from agents.adapters.base import AgentAdapter
from agents.schemas.drawing import DrawingAgentOutput, FigureDraft


class DrawingAdapter(AgentAdapter[DrawingAgentOutput]):
    agent_name = "drawing"
    state_key = "drawings"
    schema = DrawingAgentOutput
    fallback = DrawingAgentOutput(status="failed", summary="drawing output validation failed")

    def build_input(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"summary": state.get("summary", {}) or {}, "claims": state.get("claims", {}) or {}}

    def call_agent(self, state_input: dict[str, Any]) -> DrawingAgentOutput:
        claims = state_input.get("claims") or {}
        return DrawingAgentOutput(
            status="ok",
            summary="도면 adapter 골격 실행 완료",
            figures=[
                FigureDraft(
                    fig_no="도 1",
                    title="시스템 구성도",
                    type="system_architecture",
                    components=[],
                    description="요약/청구항 기반 시스템 구성도 후보",
                ),
                FigureDraft(
                    fig_no="도 2",
                    title="방법 흐름도",
                    type="flowchart",
                    components=[str(c.get("claim_no")) for c in claims.get("draft_claims", []) if isinstance(c, dict)],
                    description="독립항 구성요소 기반 방법 흐름도 후보",
                ),
            ],
            drawing_notes=["실제 SVG 렌더링 및 참조부호 배정 로직 연결 필요"],
        )
