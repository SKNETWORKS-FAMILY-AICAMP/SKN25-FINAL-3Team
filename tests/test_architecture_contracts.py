"""이 파일은 graph/state/schema/adapter 구조 계약이 깨지지 않는지 확인하는 테스트 파일이다."""
from __future__ import annotations

from typing import Any

from agents.graph import run_service_pipeline
from agents.schemas.claim import ClaimAgentOutput
from agents.schemas.drawing import DrawingAgentOutput
from agents.state import create_initial_state


class DummySummaryAdapter:
    agent_name = "summary"
    state_key = "summary"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "ok",
            "project_name": "테스트 발명",
            "readable_summary": "테스트 요약",
            "structured_invention": {"title": "테스트 발명"},
        }


class DummyComposerAdapter:
    agent_name = "composer"
    state_key = "final_package"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "ok",
            "title": state["summary"]["project_name"],
            "abstract": "최종 초록",
            "rendered_markdown": "# 최종 초안",
        }


def test_drawing_schema_matches_state_reference_numeral_contract() -> None:
    output = DrawingAgentOutput.model_validate(
        {
            "status": "ok",
            "figures": [{"fig_no": 1, "title": "도 1", "type": "flowchart"}],
            "reference_numerals": {
                "100": {
                    "number": "100",
                    "term": "사용자 단말",
                    "figure": "도 1",
                    "component_id": "C001",
                    "description": "입력 장치",
                }
            },
        }
    )

    dumped = output.model_dump(mode="json")

    assert isinstance(dumped["reference_numerals"], dict)
    assert dumped["reference_numerals"]["100"]["term"] == "사용자 단말"
    assert dumped["reference_numerals"]["100"]["figure"] == "도 1"


def test_claim_schema_accepts_minimum_pipeline_claim_and_fills_defaults() -> None:
    output = ClaimAgentOutput.model_validate(
        {
            "status": "ok",
            "draft_claims": [
                {"claim_no": 1, "text": "제1항의 테스트 청구항."},
                {"claim_no": 2, "type": "dependent", "depends_on": [1], "text": "제2항의 테스트 청구항."},
            ],
        }
    )

    claims = output.model_dump(mode="json")["draft_claims"]

    assert claims[0]["type"] == "independent"
    assert claims[0]["category"] == "method"
    assert claims[0]["depends_on"] == []
    assert claims[1]["type"] == "dependent"


def test_service_pipeline_runs_graph_through_adapters_only() -> None:
    state = run_service_pipeline(
        "사용자 입력",
        adapters={
            "summary": DummySummaryAdapter(),
            "composer": DummyComposerAdapter(),
        },
        route=("summary", "composer"),
    )

    assert state["workflow"]["status"] == "completed"
    assert state["summary"]["project_name"] == "테스트 발명"
    assert state["final_package"]["title"] == "테스트 발명"
    assert [event["agent"] for event in state["workflow"]["trace"]] == ["summary", "composer"]


def test_initial_state_keeps_top_level_slots_for_service_pipeline() -> None:
    state = create_initial_state("초기 발명 설명")

    for key in ["workflow", "summary", "prior_art", "claims", "drawings", "specification", "final_package"]:
        assert key in state
