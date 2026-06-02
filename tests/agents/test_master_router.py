"""agents/master/router.py 단위 테스트."""
from __future__ import annotations

import pytest

from agents.master.router import MasterDecision, SERVICE_PIPELINE, decide_next_agent
from agents.state import create_initial_state


# ── decide_next_agent 테스트 ────────────────────────────────────────────────

def test_no_summary_returns_run_summary():
    state = create_initial_state("발명 설명")
    decision = decide_next_agent(state)
    assert decision.status == "run_next"
    assert decision.next_agent == "summary"


def test_failed_workflow_returns_failed_immediately():
    state = create_initial_state("발명 설명")
    state["workflow"]["status"] = "failed"
    decision = decide_next_agent(state)
    assert decision.status == "failed"
    assert decision.next_agent == "end"


def test_short_user_input_returns_wait_user(state_with_summary):
    """user_input이 30자 미만이면 사용자 추가 입력을 요청해야 합니다."""
    state_with_summary["user_input"] = "너무 짧음"  # 30자 미만
    state_with_summary["summary"]["structured_invention"]["clarification_questions"] = []
    decision = decide_next_agent(state_with_summary)
    assert decision.status == "wait_user"
    assert decision.requires_user_input is True
    assert len(decision.follow_up_questions) > 0


def test_clarification_questions_returns_wait_user(state_with_summary):
    """summary가 clarification_questions를 남기면 사용자 입력을 요청해야 합니다."""
    state_with_summary["summary"]["structured_invention"]["clarification_questions"] = [
        "핵심 해결수단을 더 설명해주세요."
    ]
    decision = decide_next_agent(state_with_summary)
    assert decision.status == "wait_user"
    assert decision.requires_user_input is True
    assert "핵심 해결수단을 더 설명해주세요." in decision.follow_up_questions


def test_all_pipeline_complete_returns_completed(full_pipeline_state):
    agent_state_keys = {
        "summary": "summary",
        "prior_art": "prior_art",
        "claim": "claims",
        "drawing": "drawings",
        "specification": "specification",
        "composer": "final_package",
    }
    decision = decide_next_agent(full_pipeline_state, agent_state_keys=agent_state_keys)
    assert decision.status == "completed"
    assert decision.next_agent == "end"


def test_partial_pipeline_returns_next_missing_agent(state_with_summary):
    """summary만 있고 나머지가 없으면 다음 agent(prior_art)를 반환해야 합니다."""
    agent_state_keys = {
        "summary": "summary",
        "prior_art": "prior_art",
        "claim": "claims",
        "drawing": "drawings",
        "specification": "specification",
        "composer": "final_package",
    }
    decision = decide_next_agent(state_with_summary, agent_state_keys=agent_state_keys)
    assert decision.status == "run_next"
    assert decision.next_agent == "prior_art"


def test_requested_route_overrides_default_pipeline(state_with_summary):
    """requested_route가 있으면 SERVICE_PIPELINE 대신 그것을 따라야 합니다."""
    state_with_summary["claims"] = {}
    decision = decide_next_agent(
        state_with_summary,
        requested_route=["claim"],
        agent_state_keys={"claim": "claims"},
    )
    assert decision.next_agent == "claim"


def test_agent_state_keys_mapping_is_respected(state_with_summary):
    """state_key가 agent_name과 다른 경우(claim→claims)도 올바르게 처리해야 합니다."""
    state_with_summary["claims"] = {"status": "ok"}  # "claims" key에 저장
    agent_state_keys = {
        "summary": "summary",
        "prior_art": "prior_art",
        "claim": "claims",  # agent_name "claim" → state_key "claims"
    }
    decision = decide_next_agent(state_with_summary, agent_state_keys=agent_state_keys)
    # summary, claims 있음 → prior_art 실행
    assert decision.next_agent == "prior_art"


# ── MasterDecision 모델 테스트 ──────────────────────────────────────────────

def test_master_decision_default_values():
    decision = MasterDecision()
    assert decision.requires_user_input is False
    assert decision.follow_up_questions == []
    assert decision.route == []


def test_master_decision_serializable():
    decision = MasterDecision(
        status="completed",
        next_agent="end",
        reason="완료",
    )
    dumped = decision.model_dump(mode="json")
    assert dumped["status"] == "completed"
    assert dumped["next_agent"] == "end"


def test_service_pipeline_order():
    """SERVICE_PIPELINE이 예상 순서를 유지해야 합니다."""
    expected = ("summary", "prior_art", "claim", "drawing", "specification", "composer")
    assert SERVICE_PIPELINE == expected
