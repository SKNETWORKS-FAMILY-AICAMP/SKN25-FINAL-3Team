"""청구항 agent를 서비스 graph에 연결하는 adapter입니다.

상담 DB 기반 레거시 흐름을 제거하고, summary/prior_art state를 입력으로 받는 서비스형 계약만 유지합니다.
실제 청구항 생성기는 이 adapter의 `call_agent`에서 연결합니다.
"""
from __future__ import annotations

from typing import Any

from agents.adapters.base import AgentAdapter
from agents.schemas.claim import ClaimAgentOutput, ClaimDraft


class ClaimAdapter(AgentAdapter[ClaimAgentOutput]):
    agent_name = "claim"
    state_key = "claims"
    schema = ClaimAgentOutput
    fallback = ClaimAgentOutput(status="failed", summary="claim output validation failed")

    def build_input(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": state.get("summary", {}) or {},
            "prior_art": state.get("prior_art", {}) or {},
        }

    def call_agent(self, state_input: dict[str, Any]) -> ClaimAgentOutput:
        structured = (state_input.get("summary") or {}).get("structured_invention", {}) or {}
        solution = structured.get("solution") or structured.get("problem") or "발명의 핵심 구성을 입력 기반으로 확정하는 단계"
        return ClaimAgentOutput(
            status="ok",
            summary="청구항 adapter 골격 실행 완료",
            claim_plan={"basis": "summary.structured_invention", "strategy": "method/system/storage_medium family 후보"},
            draft_claims=[
                ClaimDraft(
                    claim_no=1,
                    type="independent",
                    category="method",
                    elements=[str(solution)],
                    text=f"{solution}을 포함하는 컴퓨터 구현 방법.",
                    source_components=[],
                )
            ],
            independent_claim_numbers=[1],
            claim_strategy_notes=["실제 청구항 문안 품질화 로직 연결 필요"],
        )
