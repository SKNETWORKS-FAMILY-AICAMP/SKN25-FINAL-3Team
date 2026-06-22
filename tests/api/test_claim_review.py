"""사용자 청구항 심사 스트리밍 API 테스트."""

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.core.state import ClaimResult, ExaminerResult, RejectionDetail
from backend.fastapi.routers import claim_review


def make_client():
    app = FastAPI()
    app.include_router(claim_review.router, prefix="/api/v1")
    return TestClient(app)


def valid_payload():
    return {
        "claim_text": "입력 데이터를 분석하여 결과를 제공하는 인공지능 시스템."
    }


def test_review_claims_streams_rewrite_and_final_result(monkeypatch):
    original = claim_review.parse_claim_text(valid_payload()["claim_text"])
    rewritten = ClaimResult(
        claims=[original.claims[0].model_copy(update={"content": "입력부와 처리부의 결합관계를 명시한 인공지능 시스템."})]
    )

    class FakeGraph:
        def stream(self, _state):
            yield {
                "examiner_node": {
                    "examiner_data": ExaminerResult(
                        is_approved=False,
                        rejections=[RejectionDetail(claims=[1], reason_text="관계가 불명확합니다.")],
                        revision_count=1,
                    )
                }
            }
            yield {"rewrite_node": {"claims_data": rewritten}}
            yield {
                "examiner_node": {
                    "examiner_data": ExaminerResult(
                        is_approved=True,
                        rejections=[],
                        revision_count=2,
                    )
                }
            }

    monkeypatch.setattr(claim_review, "build_claim_review_graph", lambda: FakeGraph())
    response = make_client().post("/api/v1/review-claims", json=valid_payload())
    events = [json.loads(line) for line in response.text.splitlines()]

    assert response.status_code == 200
    assert [event["step"] for event in events] == [
        "start", "examination", "rewrite", "examination", "done"
    ]
    assert events[-1]["approved"] is True
    assert events[-1]["was_rewritten"] is True
    assert "결합관계" in events[-1]["final_claims"][0]["content"]


def test_review_claims_rejects_too_short_content():
    payload = valid_payload()
    payload["claim_text"] = "짧음"

    response = make_client().post("/api/v1/review-claims", json=payload)

    assert response.status_code == 422


def test_parse_claim_text_infers_multiple_claims_and_dependency():
    result = claim_review.parse_claim_text(
        "청구항 1. 입력 데이터를 처리하는 프로세서를 포함하는 인공지능 시스템.\n\n"
        "청구항 2. 제1항에 있어서, 상기 프로세서는 신경망을 포함하는 인공지능 시스템."
    )

    assert len(result.claims) == 2
    assert result.claims[0].is_dependent is False
    assert result.claims[1].is_dependent is True
    assert result.claims[1].cited_claim_no == [1]
