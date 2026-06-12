"""서비스용 Master Router의 판단 로직입니다.

현재 state를 보고 다음 agent, 사용자 추가 입력 필요 여부,
재시도/종료 여부를 결정합니다. 실제 LLM 라우터는 이 규칙형 판단 뒤에 붙습니다.

─ 역할 ─
  파이프라인을 무작정 순서대로 실행하는 게 아니라,
  현재 state를 보고 "지금 뭘 해야 하는지"를 결정합니다.
  예: summary 결과가 없으면 → summary부터 실행
      summary는 있는데 설명이 너무 짧으면 → 사용자 추가 입력 요청
      모든 단계가 끝났으면 → completed 반환
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# SERVICE_PIPELINE: 기본 실행 순서
# 이 순서대로 agent가 실행됩니다.
SERVICE_PIPELINE = ("summary", "prior_art", "claim", "drawing", "specification", "composer")

# AgentRoute: decide_next_agent()가 반환할 수 있는 다음 agent 이름 목록
# "end"는 파이프라인 종료를 의미합니다.
AgentRoute = Literal["summary", "prior_art", "claim", "drawing", "specification", "composer", "end"]

# agent 이름 → state 저장 key 매핑은 adapter.state_key가 단일 기준입니다.
# Master Router는 이 값을 하드코딩하지 않고 graph/pipeline에서 전달받습니다.
# 예: ClaimAdapter.state_key = "claims"이면 state["claims"]를 확인합니다.


class MasterDecision(BaseModel):
    """프론트/API가 그대로 표시할 수 있는 다음 실행 판단 결과입니다.

    Pydantic BaseModel을 상속하므로 자동으로 타입 검증이 됩니다.
    model_dump(mode="json")으로 dict로 변환해서 state["master_decision"]에 저장합니다.
    """

    # 현재 판단 결과
    # "run_next": 다음 agent 바로 실행
    # "wait_user": 사용자 추가 입력 필요
    # "completed": 모든 단계 완료
    # "failed": 에러로 중단됨
    status: Literal["run_next", "wait_user", "completed", "failed"] = "run_next"

    next_agent: AgentRoute = "summary"  # 다음에 실행할 agent 이름 (또는 "end")
    route: list[str] = Field(default_factory=list)  # 이번 판단에서 제안하는 실행 순서
    requires_user_input: bool = False   # True면 사용자가 추가 정보를 입력해야 함
    follow_up_questions: list[str] = Field(default_factory=list)  # 사용자에게 보여줄 질문 목록
    reason: str = ""  # 이 결정을 내린 이유 (디버깅/로그용)


def _summary_missing_questions(state: dict) -> list[str]:
    """Summary agent 결과에서 사용자에게 추가로 물어봐야 할 질문을 뽑아냅니다.

    Summary agent가 발명 설명이 불충분하다고 판단하면
    state["summary"]["structured_invention"]["clarification_questions"]에
    질문 목록을 남깁니다. 이 함수는 그 질문을 꺼내서 반환합니다.

    질문이 없으면 빈 list를 반환합니다 → 파이프라인이 계속 진행됩니다.
    """
    summary = state.get("summary") or {}
    structured = summary.get("structured_invention") or {}

    # Summary agent가 남긴 clarification_questions가 있으면 그걸 씁니다.
    questions = list(structured.get("clarification_questions") or [])
    if questions:
        return questions

    # user_input이 30자 미만이면 너무 짧다고 판단해서 기본 질문을 넣습니다.
    user_input = str(state.get("user_input") or "").strip()
    if len(user_input) < 30:
        return ["해결하려는 문제, 핵심 해결수단, 기대효과를 한두 문장씩 더 알려주세요."]

    return []  # 질문 없음 → 파이프라인 계속 진행


def decide_next_agent(
    state: dict[str, Any],
    requested_route: list[str] | None = None,
    *,
    agent_state_keys: dict[str, str] | None = None,
) -> MasterDecision:
    """현재 state 기준으로 다음 실행할 agent 또는 사용자 대기 상태를 결정합니다.

    이 함수는 graph.py에서 각 agent 실행 후마다 호출됩니다.
    "지금 상태에서 뭘 해야 하는가?"를 판단하는 Master Router의 핵심 함수입니다.

    Args:
        state: 현재 PatentAgentState dict
        requested_route: 사용자가 지정한 실행 순서. 없으면 SERVICE_PIPELINE 사용.
        agent_state_keys: agent 이름 → state 저장 key 매핑.
            이 값은 build_default_adapters()의 adapter.state_key에서 만들어 전달합니다.
            즉 state key의 단일 기준은 각 adapter의 state_key입니다.

    판단 우선순위:
    1. workflow가 이미 failed 상태 → 즉시 failed 반환
    2. summary 결과가 없음 → summary부터 실행
    3. summary가 있지만 발명 설명이 부족함 → 사용자에게 추가 질문
    4. 요청된 route 중 아직 실행 안 된 agent가 있음 → 그 agent 실행
    5. 모두 완료 → completed 반환
    """
    # ── 1. 이미 실패한 상태 ──────────────────────────
    if (state.get("workflow") or {}).get("status") == "failed":
        return MasterDecision(
            status="failed",
            next_agent="end",
            reason="workflow status가 failed입니다.",
        )

    # ── 2. summary가 아직 없음 ──────────────────────
    # 파이프라인의 첫 번째 단계인 summary가 없으면 무조건 summary부터 시작합니다.
    if not state.get("summary"):
        return MasterDecision(
            status="run_next",
            next_agent="summary",
            route=["summary"],
            reason="요약 state가 없습니다.",
        )

    # ── 3. 발명 설명 불충분 → 사용자 입력 요청 ─────
    questions = _summary_missing_questions(state)
    if questions:
        return MasterDecision(
            status="wait_user",
            next_agent="end",
            requires_user_input=True,
            follow_up_questions=questions,  # 프론트엔드에 이 질문을 보여주세요
            reason="발명 정보가 부족해 추가 입력이 필요합니다.",
        )

    # ── 4. 아직 실행 안 된 agent 찾기 ──────────────
    # requested_route가 있으면 그걸 따르고, 없으면 SERVICE_PIPELINE 전체를 체크합니다.
    # state key는 adapter.state_key에서 전달된 agent_state_keys만 신뢰합니다.
    # fallback으로 agent 이름 자체를 key로 보지만, 서비스 호출부는 항상 adapter map을 넘깁니다.
    route_source = tuple(requested_route or SERVICE_PIPELINE)
    state_key_map = agent_state_keys or {}
    for agent in route_source:
        key = state_key_map.get(agent, agent)
        if not state.get(key):
            # 이 agent의 결과가 아직 state에 없음 → 이 agent를 실행해야 함
            return MasterDecision(
                status="run_next",
                next_agent=agent,
                route=[agent],
                reason=f"{agent} 결과가 아직 없습니다.",
            )

    # ── 5. 모두 완료 ────────────────────────────────
    return MasterDecision(
        status="completed",
        next_agent="end",
        reason="요청된 서비스 route가 완료되었습니다.",
    )
