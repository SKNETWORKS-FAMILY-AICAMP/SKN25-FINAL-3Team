from langgraph.graph import StateGraph, END
from core.state import PatentState
#from agents.claim_agent import ClaimGenerationAgent
#from agents.examiner_agent import ExaminerAgent

def should_continue(state: PatentState):
    """
    심사관의 평가 결과에 따라 다음 라우팅 경로를 결정합니다.
    """
    examiner_data = state.get("examiner_data")
    
    # 심사 데이터가 없으면 일단 종료
    if not examiner_data:
        return END
        
    is_approved = examiner_data.get("is_approved", False)
    revision_count = examiner_data.get("revision_count", 0)
    
    # 1. 승인되었거나
    # 2. 무한 루프 방지를 위해 수정 횟수가 2회 이상이면 그래프 종료
    if is_approved or revision_count >= 2:
        return END
    
    # 거절되었고 수정 횟수가 남아있다면 다시 청구항 생성 노드로 보냄 (수정 지시)
    return "claim_node"

def build_patent_graph():
    """
    LangGraph Workflow를 조립하고 컴파일합니다.
    """
    workflow = StateGraph(PatentState)
    
    # 인스턴스화 (나중에 에이전트 구현 후 주석 해제)
    # claim_agent = ClaimGenerationAgent()
    # examiner_agent = ExaminerAgent()
    
    # 1. 노드(Node) 등록
    # workflow.add_node("claim_node", claim_agent.run)
    # workflow.add_node("examiner_node", examiner_agent.run)
    
    # 2. 엣지(Edge) 연결
    # 요약 노드가 있다고 가정할 때, 요약 -> 청구항으로 넘어오는 시작점 설정
    workflow.set_entry_point("claim_node") 
    
    # 청구항이 생성되면 무조건 심사관에게 넘김
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