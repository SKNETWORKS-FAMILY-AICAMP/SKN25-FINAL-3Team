"""Unit tests for the examiner/rewrite-only claim review graph."""

from agents.core import claim_review_graph
from agents.core.state import ExaminerResult


def test_approved_claim_stops_without_rewrite(monkeypatch, claim_result):
    calls = []

    class Examiner:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            calls.append("examiner")
            return {
                "examiner_data": ExaminerResult(
                    is_approved=True,
                    rejections=[],
                    revision_count=1,
                )
            }

    class Rewrite:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            calls.append("rewrite")
            return {"claims_data": claim_result}

    monkeypatch.setattr(claim_review_graph, "ExaminerAgent", Examiner)
    monkeypatch.setattr(claim_review_graph, "ClaimRewriteAgent", Rewrite)

    result = claim_review_graph.build_claim_review_graph().invoke(
        {"claims_data": claim_result, "examiner_data": None}
    )

    assert calls == ["examiner"]
    assert result["examiner_data"].is_approved is True


def test_rejected_claim_is_rewritten_then_reexamined(monkeypatch, claim_result):
    calls = []

    class Examiner:
        def __init__(self, **_kwargs):
            self.count = 0

        def run(self, _state):
            self.count += 1
            calls.append("examiner")
            return {
                "examiner_data": ExaminerResult(
                    is_approved=self.count == 2,
                    rejections=[],
                    revision_count=self.count,
                )
            }

    class Rewrite:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            calls.append("rewrite")
            return {"claims_data": claim_result}

    monkeypatch.setattr(claim_review_graph, "ExaminerAgent", Examiner)
    monkeypatch.setattr(claim_review_graph, "ClaimRewriteAgent", Rewrite)

    result = claim_review_graph.build_claim_review_graph().invoke(
        {"claims_data": claim_result, "examiner_data": None}
    )

    assert calls == ["examiner", "rewrite", "examiner"]
    assert result["examiner_data"].revision_count == 2
