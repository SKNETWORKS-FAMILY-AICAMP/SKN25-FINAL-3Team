"""사용자 청구항 심사 전용 LangGraph 흐름 테스트."""

import os

os.environ["LANGCHAIN_TRACING_V2"] = "false"

from agents.core import claim_review_graph
from agents.core.state import ClaimItem, ClaimResult, ExaminerResult, RejectionDetail


def make_state():
    return {
        "mock_input_data": {},
        "summary_data": None,
        "claims_data": ClaimResult(
            claims=[
                ClaimItem(
                    claim_no=1,
                    is_dependent=False,
                    cited_claim_no=[],
                    category="시스템",
                    content="입력 데이터를 분석하여 결과를 제공하는 인공지능 시스템.",
                )
            ]
        ),
        "prior_art_data": None,
        "examiner_data": None,
    }


def test_approved_claim_stops_without_rewrite(monkeypatch):
    calls = {"examiner": 0, "rewrite": 0}

    class ApprovedExaminer:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            calls["examiner"] += 1
            return {
                "examiner_data": ExaminerResult(
                    is_approved=True,
                    rejections=[],
                    revision_count=1,
                )
            }

    class UnusedRewrite:
        def __init__(self, **_kwargs):
            pass

        def run(self, state):
            calls["rewrite"] += 1
            return {"claims_data": state["claims_data"]}

    monkeypatch.setattr(claim_review_graph, "ExaminerAgent", ApprovedExaminer)
    monkeypatch.setattr(claim_review_graph, "ClaimRewriteAgent", UnusedRewrite)

    result = claim_review_graph.build_claim_review_graph().invoke(make_state())

    assert result["examiner_data"].is_approved is True
    assert calls == {"examiner": 1, "rewrite": 0}


def test_rejected_claim_is_rewritten_and_reexamined(monkeypatch):
    calls = {"examiner": 0, "rewrite": 0}

    class RejectThenApproveExaminer:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            calls["examiner"] += 1
            approved = calls["examiner"] == 2
            return {
                "examiner_data": ExaminerResult(
                    is_approved=approved,
                    rejections=[] if approved else [
                        RejectionDetail(claims=[1], reason_text="구성요소 관계가 불명확합니다.")
                    ],
                    revision_count=calls["examiner"],
                )
            }

    class RewriteClaim:
        def __init__(self, **_kwargs):
            pass

        def run(self, state):
            calls["rewrite"] += 1
            original = state["claims_data"].claims[0]
            return {
                "claims_data": ClaimResult(
                    claims=[original.model_copy(update={"content": f"{original.content} 구성요소의 결합관계를 포함한다."})]
                )
            }

    monkeypatch.setattr(claim_review_graph, "ExaminerAgent", RejectThenApproveExaminer)
    monkeypatch.setattr(claim_review_graph, "ClaimRewriteAgent", RewriteClaim)

    result = claim_review_graph.build_claim_review_graph().invoke(make_state())

    assert result["examiner_data"].is_approved is True
    assert "결합관계" in result["claims_data"].claims[0].content
    assert calls == {"examiner": 2, "rewrite": 1}
