from langgraph.graph import StateGraph, END
from agents.core.state import PatentState
from agents.claim_agent import ClaimGenerationAgent
from agents.examiner_agent import ExaminerAgent

def should_continue(state: PatentState):
    examiner_data = state.get("examiner_data")
    if not examiner_data:
        return END
        
    is_approved = examiner_data.get("is_approved", False)
    revision_count = examiner_data.get("revision_count", 0)
    
    # 심사관이 승인했거나, 2번 이상 팅겼으면 무한루프 방지를 위해 종료
    if is_approved or revision_count >= 2:
        return END
    
    # 거절되었고 수정 횟수가 남아있다면 다시 청구항 생성 노드로 보냄 (수정 지시)
    return "claim_node"

def build_patent_graph():
    """
    LangGraph Workflow를 조립하고 컴파일합니다.
    """
    workflow = StateGraph(PatentState)

    claim_agent = ClaimGenerationAgent(model_name="gpt-4o")
    examiner_agent = ExaminerAgent(model_name="gpt-4o")
    
    # 1. 노드(Node) 등록
    workflow.add_node("claim_node", claim_agent.run)
    workflow.add_node("examiner_node", examiner_agent.run)
    
    # 2. 엣지(Edge) 연결
    workflow.set_entry_point("claim_node") 
    workflow.add_edge("claim_node", "examiner_node")
    
    # 3. 조건부 엣지(Conditional Edge) 연결
    workflow.add_conditional_edges(
        "examiner_node",
        should_continue,
        {
            "claim_node": "claim_node", # 다시 수정하러 가기
            END: END                    # 최종 완료
        }
    )
    
    return workflow.compile()