"""서비스용 Master Router의 최소 판단 로직입니다.

고정 단방향 pipeline 대신 현재 state를 보고 다음 agent, 사용자 추가 입력 필요 여부,
재시도/종료 여부를 결정합니다. 실제 LLM 라우터는 이 파일의 규칙형 판단 뒤에 붙입니다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SERVICE_PIPELINE = ("summary", "prior_art", "claim", "drawing", "specification", "composer")
AgentRoute = Literal["summary", "prior_art", "claim", "drawing", "specification", "composer", "end"]


class MasterDecision(BaseModel):
    """프론트/API가 그대로 표시할 수 있는 다음 실행 판단 결과입니다."""

    status: Literal["run_next", "wait_user", "completed", "failed"] = "run_next"
    next_agent: AgentRoute = "summary"
    route: list[str] = Field(default_factory=list)
    requires_user_input: bool = False
    follow_up_questions: list[str] = Field(default_factory=list)
    reason: str = ""


def _summary_missing_questions(state: dict) -> list[str]:
    summary = state.get("summary") or {}
    structured = summary.get("structured_invention") or {}
    questions = list(structured.get("clarification_questions") or [])
    if questions:
        return questions
    user_input = str(state.get("user_input") or "").strip()
    if len(user_input) < 30:
        return ["해결하려는 문제, 핵심 해결수단, 기대효과를 한두 문장씩 더 알려주세요."]
    return []


def decide_next_agent(state: dict, requested_route: list[str] | None = None) -> MasterDecision:
    """현재 state 기준으로 다음 실행할 agent 또는 사용자 대기 상태를 결정합니다."""
    if (state.get("workflow") or {}).get("status") == "failed":
        return MasterDecision(status="failed", next_agent="end", reason="workflow status가 failed입니다.")

    if not state.get("summary"):
        return MasterDecision(status="run_next", next_agent="summary", route=["summary"], reason="요약 state가 없습니다.")

    questions = _summary_missing_questions(state)
    if questions:
        return MasterDecision(
            status="wait_user",
            next_agent="end",
            requires_user_input=True,
            follow_up_questions=questions,
            reason="발명 정보가 부족해 추가 입력이 필요합니다.",
        )

    route_source = tuple(requested_route or SERVICE_PIPELINE)
    for agent in route_source:
        key = "claims" if agent == "claim" else "drawings" if agent == "drawing" else "final_package" if agent == "composer" else agent
        if key not in state or not state.get(key):
            return MasterDecision(status="run_next", next_agent=agent, route=[agent], reason=f"{agent} 결과가 아직 없습니다.")

    return MasterDecision(status="completed", next_agent="end", reason="요청된 서비스 route가 완료되었습니다.")
