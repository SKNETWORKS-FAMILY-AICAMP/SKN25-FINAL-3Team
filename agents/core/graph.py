from langgraph.graph import StateGraph, START, END
from agents.core.state import PatentState

from agents.claim_agent import ClaimAgent
from agents.summary_agent import SummaryAgent
#from agents.examiner_agent import ExaminerAgent

# def should_continue(state: PatentState):
#     examiner_data = state.get("examiner_data")
#     if not examiner_data:
#         return END
        
#     is_approved = examiner_data.get("is_approved", False)
#     revision_count = examiner_data.get("revision_count", 0)
    
#     if is_approved or revision_count >= 2:
#         return END
    
#     return "claim_node"

# def build_patent_graph():
#     """
#     LangGraph Workflow를 조립하고 컴파일합니다.
#     """
#     workflow = StateGraph(PatentState)

#     claim_agent = ClaimGenerationAgent(model_name="gpt-4o")
#     examiner_agent = ExaminerAgent(model_name="gpt-4o")
    
#     # 1. 노드(Node) 등록
#     workflow.add_node("claim_node", claim_agent.run)
#     workflow.add_node("examiner_node", examiner_agent.run)
    
#     # 2. 엣지(Edge) 연결
#     workflow.set_entry_point("claim_node") 
#     workflow.add_edge("claim_node", "examiner_node")
    
#     # 3. 조건부 엣지(Conditional Edge) 연결
#     workflow.add_conditional_edges(
#         "examiner_node",
#         should_continue,
#         {
#             "claim_node": "claim_node", # 다시 수정하러 가기
#             END: END                    # 최종 완료
#         }
#     )
    
#     return workflow.compile()


def build_patent_graph():
    """
    [실전 통합 그래프]
    단순 텍스트 -> (SummaryAgent) -> 구조화 데이터 -> (ClaimAgent) -> 청구항 생성
    """
    workflow = StateGraph(PatentState)

    # 1. 에이전트 초기화 (요약은 빠르고 싼 mini, 청구항은 똑똑한 4o 추천)
    summary_agent = SummaryAgent(model_name="gpt-4o-mini") 
    claim_agent = ClaimAgent(model_name="gpt-4o")
    
    # 2. 노드(Node) 등록
    workflow.add_node("summary_node", summary_agent.run)
    workflow.add_node("claim_node", claim_agent.run)
    
    # 3. 엣지(Edge) 연결 : 시작 -> 요약 -> 청구항 -> 끝
    workflow.add_edge(START, "summary_node")
    workflow.add_edge("summary_node", "claim_node")
    workflow.add_edge("claim_node", END)
    
    return workflow.compile()