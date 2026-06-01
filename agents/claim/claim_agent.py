"""서비스형 청구항 agent의 임시 안전 구현입니다.

기존 상담 DB 의존 흐름은 제거했고, 실제 청구항 생성 로직은 adapter 또는 이 파일의
`run_claim_agent` 함수에 schema 기반으로 다시 연결합니다.
"""
from __future__ import annotations

from typing import Any

from agents.schemas.claim import ClaimAgentOutput, ClaimDraft


def run_claim_agent(state_input: dict[str, Any]) -> ClaimAgentOutput:
    """summary/prior_art state를 받아 최소 청구항 output을 반환합니다."""
    summary = state_input.get("summary") or {}
    structured = summary.get("structured_invention") or {}
    solution = structured.get("solution") or structured.get("problem") or "발명의 핵심 구성"
    return ClaimAgentOutput(
        status="ok",
        summary="청구항 agent 임시 구현 실행 완료",
        draft_claims=[
            ClaimDraft(
                claim_no=1,
                type="independent",
                category="method",
                elements=[str(solution)],
                text=f"{solution}을 포함하는 컴퓨터 구현 방법.",
            )
        ],
        independent_claim_numbers=[1],
        claim_strategy_notes=["실제 청구항 품질화 로직 연결 필요"],
    )
