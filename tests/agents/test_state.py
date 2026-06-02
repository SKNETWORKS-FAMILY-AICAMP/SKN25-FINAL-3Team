"""agents/state.py 단위 테스트."""
from __future__ import annotations

import pytest

from agents.state import create_initial_state


def test_create_initial_state_workflow_status_is_idle():
    state = create_initial_state()
    assert state["workflow"]["status"] == "idle"


def test_create_initial_state_stores_user_input():
    state = create_initial_state("테스트 발명 설명")
    assert state["user_input"] == "테스트 발명 설명"


def test_create_initial_state_empty_input_by_default():
    state = create_initial_state()
    assert state["user_input"] == ""


def test_create_initial_state_workflow_current_agent_is_master():
    state = create_initial_state()
    assert state["workflow"]["current_agent"] == "master"


def test_create_initial_state_workflow_next_agent_is_summary():
    state = create_initial_state()
    assert state["workflow"]["next_agent"] == "summary"


def test_create_initial_state_workflow_trace_is_empty():
    state = create_initial_state()
    assert state["workflow"]["trace"] == []


def test_create_initial_state_workflow_errors_is_empty():
    state = create_initial_state()
    assert state["workflow"]["errors"] == []


def test_create_initial_state_agent_slots_are_empty_dicts():
    state = create_initial_state()
    for key in ("summary", "prior_art", "claims", "drawings", "specification", "final_package"):
        assert state[key] == {}, f"{key} should be empty dict"


def test_create_initial_state_document_links_has_required_keys():
    state = create_initial_state()
    links = state["document_links"]
    for key in ("term_registry", "reference_numeral_map", "claim_to_component_links"):
        assert key in links


def test_create_initial_state_drafting_options_claim_style():
    state = create_initial_state()
    assert state["drafting_options"]["claim_style"] == "korean_patent"


def test_create_initial_state_drafting_options_use_reference_numerals():
    state = create_initial_state()
    assert state["drafting_options"]["use_reference_numerals"] is True


def test_create_initial_state_max_iterations_is_8():
    state = create_initial_state()
    assert state["workflow"]["max_iterations"] == 8


def test_create_initial_state_returns_independent_objects():
    """두 번 호출하면 독립적인 객체가 반환돼야 합니다."""
    s1 = create_initial_state()
    s2 = create_initial_state()
    s1["workflow"]["errors"].append("오류")
    assert s2["workflow"]["errors"] == []
