"""agents/graph.py 단위 테스트 (mock adapter 사용)."""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from agents.graph import (
    build_agent_state_key_map,
    build_default_adapters,
    run_service_pipeline,
)
from agents.state import create_initial_state
from agents.validation import AgentValidationError


# ── build_default_adapters 테스트 ────────────────────────────────────────────

def test_build_default_adapters_contains_all_six_agents():
    adapters = build_default_adapters()
    expected = {"summary", "prior_art", "claim", "drawing", "specification", "composer"}
    assert set(adapters.keys()) == expected


def test_build_default_adapters_values_have_agent_name():
    adapters = build_default_adapters()
    for name, adapter in adapters.items():
        assert adapter.agent_name == name


# ── build_agent_state_key_map 테스트 ─────────────────────────────────────────

def test_build_agent_state_key_map_claim_maps_to_claims():
    adapters = build_default_adapters()
    key_map = build_agent_state_key_map(adapters)
    assert key_map["claim"] == "claims"


def test_build_agent_state_key_map_summary_maps_to_summary():
    adapters = build_default_adapters()
    key_map = build_agent_state_key_map(adapters)
    assert key_map["summary"] == "summary"


def test_build_agent_state_key_map_composer_maps_to_final_package():
    adapters = build_default_adapters()
    key_map = build_agent_state_key_map(adapters)
    assert key_map["composer"] == "final_package"


# ── run_service_pipeline 테스트 ───────────────────────────────────────────────

@pytest.fixture
def full_mock_adapters(make_mock_adapter):
    """6개 agent mock adapter를 모두 포함한 dict를 반환합니다."""
    pipeline = [
        ("summary", "summary"),
        ("prior_art", "prior_art"),
        ("claim", "claims"),
        ("drawing", "drawings"),
        ("specification", "specification"),
        ("composer", "final_package"),
    ]
    return {name: make_mock_adapter(name, key) for name, key in pipeline}


def test_run_pipeline_with_mock_adapters_status_completed(full_mock_adapters):
    state = run_service_pipeline("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.", full_mock_adapters)
    assert state["workflow"]["status"] == "completed"


def test_run_pipeline_with_mock_adapters_all_agents_called(full_mock_adapters):
    run_service_pipeline("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.", full_mock_adapters)
    for adapter in full_mock_adapters.values():
        adapter.run.assert_called_once()


def test_run_pipeline_results_stored_in_state(full_mock_adapters):
    state = run_service_pipeline("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.", full_mock_adapters)
    assert state["summary"] == {"status": "ok", "summary": "summary 결과"}
    assert state["claims"] == {"status": "ok", "summary": "claim 결과"}


def test_run_pipeline_partial_route_only_runs_specified_agents(full_mock_adapters):
    run_service_pipeline(
        "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.",
        full_mock_adapters,
        route=["summary"],
    )
    full_mock_adapters["summary"].run.assert_called_once()
    full_mock_adapters["prior_art"].run.assert_not_called()
    full_mock_adapters["claim"].run.assert_not_called()


def test_run_pipeline_adapter_validation_error_sets_status_failed(full_mock_adapters):
    full_mock_adapters["summary"].run.side_effect = AgentValidationError(
        agent_name="summary",
        schema_name="SummaryAgentOutput",
        validation_errors=[{"msg": "field required"}],
        raw_output={},
    )
    state = run_service_pipeline("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.", full_mock_adapters)
    assert state["workflow"]["status"] == "failed"
    assert any("summary" in e for e in state["workflow"]["errors"])


def test_run_pipeline_unexpected_exception_sets_status_failed(full_mock_adapters):
    full_mock_adapters["claim"].run.side_effect = RuntimeError("예상치 못한 오류")
    state = run_service_pipeline(
        "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.",
        full_mock_adapters,
        route=["summary", "prior_art", "claim"],
    )
    assert state["workflow"]["status"] == "failed"


def test_run_pipeline_progress_callback_called_for_each_agent(full_mock_adapters):
    callback = MagicMock()
    run_service_pipeline(
        "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.",
        full_mock_adapters,
        progress_callback=callback,
    )
    called_names = [c.args[0] for c in callback.call_args_list]
    for name in full_mock_adapters:
        assert name in called_names


def test_run_pipeline_unregistered_adapter_records_error(full_mock_adapters):
    state = run_service_pipeline(
        "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.",
        full_mock_adapters,
        route=["nonexistent_agent"],
    )
    assert any("nonexistent_agent" in e for e in state["workflow"]["errors"])


def test_run_pipeline_continues_from_initial_state(full_mock_adapters):
    """initial_state를 넘기면 이어서 실행해야 합니다."""
    existing = create_initial_state("기존 입력")
    existing["summary"] = {"status": "ok", "summary": "기존 요약"}

    state = run_service_pipeline(
        "기존 입력",
        full_mock_adapters,
        initial_state=existing,
        route=["prior_art"],
    )
    full_mock_adapters["summary"].run.assert_not_called()
    full_mock_adapters["prior_art"].run.assert_called_once()
