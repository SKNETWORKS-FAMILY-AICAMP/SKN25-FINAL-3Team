"""Unit tests for the claim-generation NDJSON worker contract."""

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.core.state import ExaminerResult, PriorArtCandidate, PriorArtResult
from backend.fastapi.routers import claims


def make_client():
    app = FastAPI()
    app.include_router(claims.router, prefix="/api/v1")
    return TestClient(app)


def test_safe_serialize_supports_pydantic_and_plain_object_fallbacks(claim_result):
    class Plain:
        def __init__(self):
            self.value = 3

    assert claims.safe_serialize(claim_result)["claims"][0]["claim_no"] == 1
    assert claims.safe_serialize({"a": 1}) == "{'a': 1}"
    assert claims.safe_serialize(Plain()) == {"value": 3}


def test_generate_claims_streams_state_prior_art_and_done(
    monkeypatch,
    parsed_invention,
    claim_result,
):
    class FakeGraph:
        def stream(self, _state, config):
            assert config["run_name"] == "Patent_Claims_Generation"
            yield {"summary_node": {"summary_data": parsed_invention}}
            yield {"claim_node": {"claims_data": claim_result}}
            yield {
                "examiner_node": {
                    "examiner_data": ExaminerResult(
                        is_approved=True,
                        rejections=[],
                        revision_count=1,
                    )
                }
            }

    prior_art = PriorArtResult(
        candidates=[PriorArtCandidate(patent_id=1, rank=1, title="선행특허")],
        overall_risk={"level": "low"},
        analysis_summary="저촉 가능성이 낮다.",
        search_source="LOCAL_DB",
    )

    async def fake_judge(**_kwargs):
        return None

    monkeypatch.setattr(claims, "build_patent_graph", lambda: FakeGraph())
    monkeypatch.setattr(
        claims,
        "run_prior_art_agent",
        lambda _state, _top_n: {"prior_art_data": prior_art},
    )
    monkeypatch.setattr(claims, "background_llm_judge", fake_judge)

    response = make_client().post(
        "/api/v1/generate-claims",
        json={"initial_state": {"mock_input_data": {"title": "발명"}}},
    )
    events = [json.loads(line) for line in response.text.splitlines()]

    assert response.status_code == 200
    assert [event["step"] for event in events] == [
        "start",
        "log_and_state",
        "summary",
        "log_and_state",
        "claim",
        "log_and_state",
        "examiner",
        "prior_art_start",
        "prior_art_done",
        "done",
    ]
    assert events[-1]["claims"][0]["claim_no"] == 1
    assert events[-1]["prior_art_data"]["overall_risk"]["level"] == "low"


def test_generate_claims_continues_when_prior_art_lookup_fails(
    monkeypatch,
    claim_result,
):
    class FakeGraph:
        def stream(self, _state, config=None):
            yield {"claim_node": {"claims_data": claim_result}}
            yield {
                "examiner_node": {
                    "examiner_data": ExaminerResult(
                        is_approved=True,
                        rejections=[],
                        revision_count=0,
                    )
                }
            }

    def fail_prior_art(*_args):
        raise RuntimeError("search unavailable")

    async def fake_judge(**_kwargs):
        return None

    monkeypatch.setattr(claims, "build_patent_graph", lambda: FakeGraph())
    monkeypatch.setattr(claims, "run_prior_art_agent", fail_prior_art)
    monkeypatch.setattr(claims, "background_llm_judge", fake_judge)

    response = make_client().post(
        "/api/v1/generate-claims",
        json={"initial_state": {"mock_input_data": {"title": "발명"}}},
    )
    events = [json.loads(line) for line in response.text.splitlines()]

    assert events[-1]["step"] == "done"
    assert events[-1]["prior_art_data"] is None
