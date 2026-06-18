"""agents/summary/adapter.py 단위 테스트."""
from __future__ import annotations

import pytest

from agents.schemas.summary import SummaryAgentOutput
from agents.state import create_initial_state
from agents.summary.adapter import SummaryAdapter


@pytest.fixture
def adapter() -> SummaryAdapter:
    return SummaryAdapter()


def test_adapter_agent_name(adapter):
    assert adapter.agent_name == "summary"


def test_adapter_state_key(adapter):
    assert adapter.state_key == "summary"


def test_adapter_schema_is_summary_agent_output(adapter):
    assert adapter.schema is SummaryAgentOutput


def test_build_input_extracts_user_input(adapter):
    state = create_initial_state("테스트 발명 설명입니다.")
    inp = adapter.build_input(state)
    assert inp["user_input"] == "테스트 발명 설명입니다."


def test_build_input_extracts_existing_summary(adapter):
    state = create_initial_state()
    state["summary"] = {"status": "ok", "summary": "기존 요약"}
    inp = adapter.build_input(state)
    assert inp["summary"] == {"status": "ok", "summary": "기존 요약"}


def test_call_agent_long_input_returns_ok_status(adapter):
    state = create_initial_state("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.")
    inp = adapter.build_input(state)
    result = adapter.call_agent(inp)
    assert result.status == "ok"
    assert result.warnings == []


def test_call_agent_short_input_returns_needs_user_input(adapter):
    state = create_initial_state("너무 짧음")
    inp = adapter.build_input(state)
    result = adapter.call_agent(inp)
    assert result.status == "needs_user_input"
    assert len(result.warnings) > 0


def test_call_agent_short_input_has_clarification_questions(adapter):
    state = create_initial_state("짧음")
    inp = adapter.build_input(state)
    result = adapter.call_agent(inp)
    questions = result.structured_invention.clarification_questions
    assert len(questions) > 0


def test_run_returns_dict(adapter):
    """adapter.run()이 dict를 반환해야 합니다."""
    state = create_initial_state("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.")
    result = adapter.run(state)
    assert isinstance(result, dict)
    assert "status" in result


def test_run_output_validates_against_schema(adapter):
    """run() 결과가 SummaryAgentOutput 스키마를 통과해야 합니다."""
    state = create_initial_state("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.")
    result = adapter.run(state)
    # dict로 반환된 결과를 다시 검증
    validated = SummaryAgentOutput.model_validate(result)
    assert validated.status in ("ok", "needs_user_input")
