"""Unit tests for deterministic specification parsing and validation helpers."""

from agents.specification import spec_helpers
from agents.specification.specification_agent import extract_specification_state


def test_safe_parse_json_extracts_fenced_object():
    assert spec_helpers.safe_parse_json('text ```json\n{"ok": true}\n```') == {
        "ok": True
    }


def test_safe_parse_json_returns_none_for_invalid_content():
    assert spec_helpers.safe_parse_json("not-json") is None


def test_reference_and_publication_number_detection():
    text = "제어부(110)는 KR 10-2024-0012345 A 문헌을 참조한다."

    assert spec_helpers.detect_reference_numerals(text) == {"110"}
    assert "KR1020240012345A" in spec_helpers.detect_publication_numbers(text)


def test_normalize_reference_numerals_accepts_list_shape():
    result = spec_helpers.normalize_reference_numerals(
        [{"number": 110, "label": "제어부", "figure": "도 1"}]
    )

    assert result == {
        "110": {
            "number": "110",
            "term": "제어부",
            "figure": "도 1",
            "component_id": "",
            "description": "",
        }
    }


def test_deduplicate_list_handles_equal_dicts():
    assert spec_helpers.deduplicate_list([{"a": 1}, {"a": 1}, "x", "x"]) == [
        {"a": 1},
        "x",
    ]


def test_merge_prior_art_candidate_extras_updates_and_appends():
    result = spec_helpers.merge_prior_art_candidate_extras(
        [{"patent_id": "A", "title": "기존"}],
        [
            {"patent_id": "A", "summary": "보강"},
            {"patent_id": "B", "title": "추가"},
        ],
    )

    assert result == [
        {"patent_id": "A", "title": "기존", "summary": "보강"},
        {"patent_id": "B", "title": "추가"},
    ]


def test_build_specification_material_combines_current_state_sections():
    state = {
        "consultation": {
            "invention_title": "데이터 분석 시스템",
            "problem": "느린 탐지",
            "solution": [{"description": "분석 모듈"}],
            "components": [{"name": "분석 모듈", "aliases": ["분석부"]}],
        },
        "claims": {
            "draft_claims": [
                {"claim_no": 1, "type": "independent", "elements": ["분석 모듈"]}
            ],
            "independent_claim_numbers": [1],
        },
        "drawings": {
            "reference_numerals": [{"number": "110", "term": "분석 모듈"}]
        },
    }

    material = spec_helpers.build_specification_material(state)

    assert material.invention_title == "데이터 분석 시스템"
    assert material.solution == "분석 모듈"
    assert material.allowed_ref_numerals == {"110"}
    assert material.allowed_terms["분석부"] == "분석 모듈"


def test_detect_repeated_phrases_finds_repeated_word_and_sequence():
    issues = spec_helpers.detect_repeated_phrases("제어부 제어부 데이터 처리 데이터 처리")

    assert "제어부 제어부" in issues
    assert "데이터 처리" in issues


def test_validate_specification_reports_required_sections():
    material = spec_helpers.SpecificationMaterial()

    result = spec_helpers.validate_specification({}, {}, {}, material)

    assert result.passed is False
    assert any("technical_field" in issue for issue in result.issues)


def test_extract_specification_state_normalizes_note_string_to_list():
    result = extract_specification_state(
        {"technical_field": "데이터 처리 분야", "embodiment_notes": "근거 부족"}
    )

    assert result["technical_field"] == "데이터 처리 분야"
    assert result["embodiment_notes"] == ["근거 부족"]
