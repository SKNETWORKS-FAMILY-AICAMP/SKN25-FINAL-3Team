"""Unit tests for individual agents with every external model mocked."""

from langchain_core.runnables import RunnableLambda

from agents.claim_agent import ClaimAgent
from agents.claim_rewrite_agent import ClaimRewriteAgent
from agents.drawing_agent import SmartDrawingAgent
from agents.paper_analyzer import PaperAnalyzerAgent, PaperMockData
from agents.summary_agent import SummaryAgent
from agents.core.state import PatentDrawing


def _without_init(cls, runnable=None):
    instance = cls.__new__(cls)
    if runnable is not None:
        instance.structured_llm = runnable
    return instance


def test_summary_agent_returns_none_for_empty_input():
    agent = _without_init(SummaryAgent)

    assert agent.run({"mock_input_data": {}}) == {"summary_data": None}


def test_summary_agent_returns_structured_result(parsed_invention, patent_state):
    agent = _without_init(
        SummaryAgent,
        RunnableLambda(lambda _prompt: parsed_invention),
    )

    result = agent.run({"mock_input_data": patent_state["mock_input_data"]})

    assert result["summary_data"] == parsed_invention


def test_summary_agent_converts_model_error_to_none(patent_state):
    def fail(_prompt):
        raise RuntimeError("model unavailable")

    agent = _without_init(SummaryAgent, RunnableLambda(fail))

    assert agent.run({"mock_input_data": patent_state["mock_input_data"]}) == {
        "summary_data": None
    }


def test_claim_agent_requires_summary_data():
    agent = _without_init(ClaimAgent)

    assert agent.run({"summary_data": None}) == {"claims_data": None}


def test_claim_agent_returns_structured_claims(parsed_invention, claim_result):
    agent = _without_init(ClaimAgent, RunnableLambda(lambda _prompt: claim_result))

    result = agent.run({"summary_data": parsed_invention})

    assert result["claims_data"] == claim_result


def test_claim_agent_converts_model_error_to_none(parsed_invention):
    agent = _without_init(
        ClaimAgent,
        RunnableLambda(lambda _prompt: (_ for _ in ()).throw(RuntimeError("boom"))),
    )

    assert agent.run({"summary_data": parsed_invention}) == {"claims_data": None}


def test_rewrite_agent_formats_independent_and_dependent_claims(claim_result):
    agent = _without_init(ClaimRewriteAgent)

    formatted = agent._format_original_claims(claim_result)

    assert "[제1항] (독립항)" in formatted
    assert "[제2항] (제1항을 인용하는 종속항)" in formatted


def test_rewrite_agent_formats_dict_rejections():
    agent = _without_init(ClaimRewriteAgent)

    formatted = agent._format_rejections(
        {"rejections": [{"claims": [1, 2], "reason_text": "관계 불명확"}]}
    )

    assert "대상 청구항: [1, 2]" in formatted
    assert "관계 불명확" in formatted


def test_rewrite_agent_keeps_original_when_required_input_missing(claim_result):
    agent = _without_init(ClaimRewriteAgent)

    assert agent.run({"claims_data": claim_result, "examiner_data": None}) == {
        "claims_data": claim_result
    }


def test_rewrite_agent_returns_model_result(claim_result, rejected_examiner_result):
    agent = _without_init(
        ClaimRewriteAgent,
        RunnableLambda(lambda _prompt: claim_result),
    )

    result = agent.run(
        {"claims_data": claim_result, "examiner_data": rejected_examiner_result}
    )

    assert result["claims_data"] == claim_result


def test_paper_analyzer_returns_empty_for_blank_text():
    agent = _without_init(PaperAnalyzerAgent)

    assert agent.extract_from_paper("") == {}


def test_paper_analyzer_removes_references_before_model_call():
    captured = {}
    output = PaperMockData(
        title="분석 시스템",
        prior_art_problem="문제",
        problem_to_solve="과제",
        core_tech="기술",
        expected_effect="효과",
    )

    def invoke(prompt):
        captured["prompt"] = prompt.to_messages()[-1].content
        return output

    agent = _without_init(PaperAnalyzerAgent, RunnableLambda(invoke))

    result = agent.extract_from_paper("본문 기술\n\nReferences\n인용 문헌")

    assert result["title"] == "분석 시스템"
    assert "본문 기술" in captured["prompt"]
    assert "인용 문헌" not in captured["prompt"]


def test_drawing_agent_requires_summary_data():
    agent = SmartDrawingAgent.__new__(SmartDrawingAgent)

    assert agent.run({}) == {"drawing_spec": None}


def test_drawing_agent_builds_two_drawings_and_reference_map(monkeypatch, parsed_invention):
    agent = SmartDrawingAgent.__new__(SmartDrawingAgent)
    agent.output_dir = "/tmp"
    agent.font_name = "NanumGothic"

    def fake_render(dot, _prefix, fig_no, title, diagram_type):
        return PatentDrawing(
            fig_no=fig_no,
            title=title,
            diagram_type=diagram_type,
            dot_code=dot.source,
            image_path=f"/tmp/{fig_no}.png",
        )

    monkeypatch.setattr(agent, "_render", fake_render)

    spec = agent.run({"summary_data": parsed_invention})["drawing_spec"]

    assert [drawing.diagram_type for drawing in spec.drawings] == [
        "BLOCK_DIAGRAM",
        "FLOWCHART",
    ]
    assert {ref.numeral for ref in spec.reference_numerals} == {"110", "S210"}
