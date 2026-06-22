"""Unit tests for the current Pydantic and LangGraph state contracts."""

import pytest
from pydantic import ValidationError

from agents.core.state import (
    ClaimItem,
    PatentDrawing,
    PatentState,
    PriorArtCandidate,
    PriorArtResult,
)


def test_parsed_invention_round_trips_without_losing_nested_data(parsed_invention):
    restored = type(parsed_invention).model_validate(parsed_invention.model_dump())

    assert restored.invention_metadata.title == "센서 데이터를 분석하는 시스템"
    assert restored.architecture.components[0].id == "COMP_001"
    assert restored.architecture.processing_steps[0].input_data_ids == ["FLOW_001"]


def test_component_parent_id_defaults_to_none(parsed_invention):
    assert parsed_invention.architecture.components[0].parent_id is None


@pytest.mark.parametrize("category", ["방법", "시스템", "CRM"])
def test_claim_item_accepts_supported_categories(category):
    claim = ClaimItem(
        claim_no=1,
        is_dependent=False,
        cited_claim_no=[],
        category=category,
        content="청구항 내용",
    )

    assert claim.category == category


def test_claim_item_rejects_unknown_category():
    with pytest.raises(ValidationError):
        ClaimItem(
            claim_no=1,
            is_dependent=False,
            cited_claim_no=[],
            category="장치",
            content="청구항 내용",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [("rank", 0), ("score", -0.1), ("score", 1.1)],
)
def test_prior_art_candidate_enforces_rank_and_score_ranges(field, value):
    data = {"patent_id": 1, "rank": 1, "score": 0.5}
    data[field] = value

    with pytest.raises(ValidationError):
        PriorArtCandidate(**data)


def test_prior_art_result_default_lists_are_independent():
    first = PriorArtResult()
    second = PriorArtResult()

    first.candidates.append(PriorArtCandidate(patent_id=1, rank=1))

    assert len(first.candidates) == 1
    assert second.candidates == []


def test_patent_drawing_rejects_unsupported_diagram_type():
    with pytest.raises(ValidationError):
        PatentDrawing(
            fig_no="도 1",
            title="구성도",
            diagram_type="SEQUENCE",
            dot_code="digraph {}",
            image_path="/tmp/test.png",
        )


def test_patent_state_declares_current_pipeline_slots():
    assert set(PatentState.__annotations__) == {
        "mock_input_data",
        "summary_data",
        "claims_data",
        "prior_art_data",
        "examiner_data",
    }
