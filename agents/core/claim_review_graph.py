"""사용자가 작성한 청구항을 심사하고 필요한 경우 보정하는 전용 그래프."""

from langgraph.graph import END, START, StateGraph

from agents.claim_rewrite_agent import ClaimRewriteAgent
from agents.core.graph import should_continue
from agents.core.state import PatentState
from agents.examiner import ExaminerAgent


def build_claim_review_graph():
    """기존 심사관/보정 에이전트만 재사용하는 독립 청구항 심사 그래프를 만든다."""
    workflow = StateGraph(PatentState)

    examiner_agent = ExaminerAgent(model_name="gpt-4o")
    rewrite_agent = ClaimRewriteAgent(model_name="gpt-5.4-mini")

    workflow.add_node("examiner_node", examiner_agent.run)
    workflow.add_node("rewrite_node", rewrite_agent.run)

    workflow.add_edge(START, "examiner_node")
    workflow.add_conditional_edges(
        "examiner_node",
        should_continue,
        {
            "rewrite_node": "rewrite_node",
            END: END,
        },
    )
    workflow.add_edge("rewrite_node", "examiner_node")

    return workflow.compile()
