"""agents/validation.py 단위 테스트."""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from agents.validation import (
    AgentValidationError,
    normalize_to_schema_shape,
    safe_validate_output,
)


# ── 테스트용 스키마 ─────────────────────────────────────────────────────────

class SimpleSchema(BaseModel):
    name: str
    tags: list[str] = []
    count: Optional[int] = None


class NestedItem(BaseModel):
    title: str
    value: int = 0


class NestedSchema(BaseModel):
    label: str
    items: list[NestedItem] = []


# ── normalize_to_schema_shape 테스트 ────────────────────────────────────────

def test_normalize_str_field_none_becomes_empty_string():
    raw = {"name": None, "tags": []}
    result = normalize_to_schema_shape(raw, SimpleSchema)
    assert result["name"] == ""


def test_normalize_str_field_list_becomes_joined_string():
    raw = {"name": ["부분1", "부분2"], "tags": []}
    result = normalize_to_schema_shape(raw, SimpleSchema)
    assert result["name"] == "부분1, 부분2"


def test_normalize_str_field_dict_becomes_semicolon_string():
    raw = {"name": {"key": "val"}, "tags": []}
    result = normalize_to_schema_shape(raw, SimpleSchema)
    assert result["name"] == "key: val"


def test_normalize_list_field_none_becomes_empty_list():
    raw = {"name": "test", "tags": None}
    result = normalize_to_schema_shape(raw, SimpleSchema)
    assert result["tags"] == []


def test_normalize_list_field_single_string_becomes_list():
    raw = {"name": "test", "tags": "단일태그"}
    result = normalize_to_schema_shape(raw, SimpleSchema)
    assert result["tags"] == ["단일태그"]


def test_normalize_nested_model_string_to_dict():
    """list[NestedItem]에서 문자열 항목이 {title: str} dict로 변환돼야 합니다."""
    raw = {"label": "테스트", "items": ["제목A", "제목B"]}
    result = normalize_to_schema_shape(raw, NestedSchema)
    assert result["items"][0]["title"] == "제목A"
    assert result["items"][1]["title"] == "제목B"


def test_normalize_already_valid_dict_unchanged():
    raw = {"name": "정상입력", "tags": ["a", "b"]}
    result = normalize_to_schema_shape(raw, SimpleSchema)
    assert result["name"] == "정상입력"
    assert result["tags"] == ["a", "b"]


def test_normalize_pydantic_instance_returned_as_is():
    instance = SimpleSchema(name="이미 모델")
    result = normalize_to_schema_shape(instance, SimpleSchema)
    assert result is instance


# ── safe_validate_output 테스트 ─────────────────────────────────────────────

def test_safe_validate_output_valid_data_returns_model():
    result = safe_validate_output(
        agent_name="test_agent",
        schema=SimpleSchema,
        raw_output={"name": "유효한 입력", "tags": ["a"]},
    )
    assert isinstance(result, SimpleSchema)
    assert result.name == "유효한 입력"


def test_safe_validate_output_normalize_handles_none_and_str():
    """normalize가 None→"", str→list 변환을 처리하므로 검증을 통과해야 합니다."""
    result = safe_validate_output(
        agent_name="test_agent",
        schema=SimpleSchema,
        raw_output={"name": None, "tags": "단일태그"},
    )
    assert result.name == ""
    assert result.tags == ["단일태그"]


def test_safe_validate_output_missing_required_field_raises():
    with pytest.raises(AgentValidationError) as exc_info:
        safe_validate_output(
            agent_name="claim_agent",
            schema=SimpleSchema,
            raw_output={},  # name 필드가 없고 normalize로도 채울 수 없음
        )
    err = exc_info.value
    assert err.agent_name == "claim_agent"
    assert err.schema_name == "SimpleSchema"
    assert len(err.validation_errors) > 0


def test_safe_validate_output_repair_not_called_by_default(mocker):
    mock_repair = mocker.MagicMock()
    with pytest.raises(AgentValidationError):
        safe_validate_output(
            agent_name="test_agent",
            schema=SimpleSchema,
            raw_output={},
            repair_fn=mock_repair,
            enable_llm_repair=False,
        )
    mock_repair.assert_not_called()


def test_safe_validate_output_repair_called_when_enabled(mocker):
    mock_repair = mocker.MagicMock(return_value={"name": "repair된 결과"})
    result = safe_validate_output(
        agent_name="test_agent",
        schema=SimpleSchema,
        raw_output={},
        repair_fn=mock_repair,
        enable_llm_repair=True,
    )
    mock_repair.assert_called_once()
    assert result.name == "repair된 결과"


# ── AgentValidationError 테스트 ─────────────────────────────────────────────

def test_agent_validation_error_message_contains_agent_name():
    err = AgentValidationError(
        agent_name="summary",
        schema_name="SummaryAgentOutput",
        validation_errors=[{"msg": "field required"}],
        raw_output={},
    )
    assert "summary" in str(err)


def test_agent_validation_error_message_contains_rerun_hint():
    err = AgentValidationError(
        agent_name="claim",
        schema_name="ClaimAgentOutput",
        validation_errors=[],
        raw_output={},
    )
    assert "/api/agents/claim/run" in str(err)


def test_agent_validation_error_repair_error_in_message():
    err = AgentValidationError(
        agent_name="drawing",
        schema_name="DrawingOutput",
        validation_errors=[],
        raw_output={},
        repair_error="OpenAI timeout",
    )
    assert "OpenAI timeout" in str(err)
    assert err.repair_error == "OpenAI timeout"
