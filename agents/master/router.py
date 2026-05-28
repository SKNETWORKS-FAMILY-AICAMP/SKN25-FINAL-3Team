"""이 파일은 현재 state를 보고 다음 실행 agent를 결정하는 master router 파일이다.

초기 구조 단계에서는 LLM router 대신 명시적 규칙만 두고,
나중에 LLM master가 같은 결정 스키마를 반환하도록 교체할 수 있다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from agents.state import PatentAgentState

RouteName = Literal[
    "consultation",
    "summary",
    "prior_art",
    "claim",
    "drawing",
    "specification",
    "composer",
    "review",
    "end",
]


class MasterRouteDecision(BaseModel):
    next_agent: RouteName
    reason: str = ""
    requires_user_input: bool = False
    missing_slots: list[str] = Field(default_factory=list)


REQUIRED_SUMMARY_FIELDS = (
    "problem_to_solve",
    "core_technology",
    "expected_effect",
)


def decide_next_agent(state: PatentAgentState) -> MasterRouteDecision:
    """현재 state 기준 다음 agent를 결정한다.

    - 사용자 입력/요약 핵심 슬롯이 부족하면 consultation으로 보낸다.
    - 아직 summary가 비어 있으면 summary.
    - 이후 산출물 존재 여부에 따라 단방향 순서를 진행한다.
    """

    summary = state.get("summary", {}) or {}
    missing = [field for field in REQUIRED_SUMMARY_FIELDS if not str(summary.get(field, "")).strip()]
    if missing:
        return MasterRouteDecision(
            next_agent="consultation",
            reason="핵심 발명 입력이 부족해 추가 질문이 필요함",
            requires_user_input=True,
            missing_slots=missing,
        )
    if not summary.get("readable_summary"):
        return MasterRouteDecision(next_agent="summary", reason="요약 산출물 없음")
    if not (state.get("prior_art", {}) or {}).get("candidates"):
        return MasterRouteDecision(next_agent="prior_art", reason="선행기술 후보 없음")
    if not (state.get("claims", {}) or {}).get("draft_claims"):
        return MasterRouteDecision(next_agent="claim", reason="청구항 초안 없음")
    if not (state.get("drawings", {}) or {}).get("figures"):
        return MasterRouteDecision(next_agent="drawing", reason="도면 초안 없음")
    if not (state.get("specification", {}) or {}).get("detailed_description"):
        return MasterRouteDecision(next_agent="specification", reason="명세서 상세설명 없음")
    if not state.get("final_package"):
        return MasterRouteDecision(next_agent="composer", reason="최종 패키지 없음")
    return MasterRouteDecision(next_agent="end", reason="필수 산출물 생성 완료")
