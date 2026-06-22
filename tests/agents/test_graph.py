"""Unit tests for the current patent LangGraph routing."""

import pytest
from langgraph.graph import END

from agents.core import graph
from agents.core.state import ExaminerResult


@pytest.mark.parametrize(
    "examiner_data",
    [
        None,
        {"is_approved": True, "revision_count": 0},
        {"is_approved": False, "revision_count": 2},
        ExaminerResult(is_approved=True, rejections=[], revision_count=1),
        ExaminerResult(is_approved=False, rejections=[], revision_count=2),
    ],
)
def test_should_continue_ends_for_missing_approved_or_exhausted_result(examiner_data):
    assert graph.should_continue({"examiner_data": examiner_data}) == END


@pytest.mark.parametrize(
    "examiner_data",
    [
        {"is_approved": False, "revision_count": 0},
        ExaminerResult(is_approved=False, rejections=[], revision_count=1),
    ],
)
def test_should_continue_routes_rejected_claims_to_rewrite(examiner_data):
    assert graph.should_continue({"examiner_data": examiner_data}) == "rewrite_node"


def test_build_patent_graph_registers_current_nodes(monkeypatch):
    class DummyAgent:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            return {}

    for name in ("SummaryAgent", "ClaimAgent", "ExaminerAgent", "ClaimRewriteAgent"):
        monkeypatch.setattr(graph, name, DummyAgent)

    compiled = graph.build_patent_graph()

    assert set(compiled.get_graph().nodes) == {
        "__start__",
        "summary_node",
        "claim_node",
        "examiner_node",
        "rewrite_node",
        "__end__",
    }


def test_compiled_graph_runs_summary_claim_and_examiner_in_order(monkeypatch):
    calls = []

    class Summary:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            calls.append("summary")
            return {"summary_data": None}

    class Claim:
        def __init__(self, **_kwargs):
            pass

        def run(self, _state):
            calls.append("claim")
            return {"claims_data": None}

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
            return {}

    monkeypatch.setattr(graph, "SummaryAgent", Summary)
    monkeypatch.setattr(graph, "ClaimAgent", Claim)
    monkeypatch.setattr(graph, "ExaminerAgent", Examiner)
    monkeypatch.setattr(graph, "ClaimRewriteAgent", Rewrite)

    result = graph.build_patent_graph().invoke({"mock_input_data": {"title": "발명"}})

    assert calls == ["summary", "claim", "examiner"]
    assert result["examiner_data"].is_approved is True
