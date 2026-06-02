from langgraph.graph import StateGraph, START, END
from agents.core.state import PatentState

from agents.claim_agent import ClaimAgent
from agents.summary_agent import SummaryAgent
from agents.examiner import ExaminerAgent
from agents.claim_rewrite_agent import ClaimRewriteAgent

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

def should_continue(state: PatentState):
    """
    심사관의 결과를 보고 끝낼지, 다시 수정(Rewrite)할지 결정하는 신호등 함수
    """
    examiner_data = state.get("examiner_data")
    if not examiner_data:
        return END
        
    # 💡 [핵심] 딕셔너리로 들어오든, Pydantic 객체로 들어오든 유연하게 꺼냅니다.
    if isinstance(examiner_data, dict):
        is_approved = examiner_data.get("is_approved", False)
        revision_count = examiner_data.get("revision_count", 0)
    else:
        is_approved = examiner_data.is_approved
        revision_count = examiner_data.revision_count
    
    # 승인(통과)되었거나, 2번 이상 수정을 반복했다면 강제 종료!
    if is_approved or revision_count >= 2:
        return END
    
    # 거절당했으면 수정하러 가기
    return "rewrite_node"

def build_patent_graph():
    workflow = StateGraph(PatentState)

    # 1. 에이전트 장전
    summary_agent = SummaryAgent(model_name="gpt-4o-mini")
    claim_agent = ClaimAgent(model_name="gpt-4o")
    examiner_agent = ExaminerAgent(model_name="gpt-4o")
    rewrite_agent = ClaimRewriteAgent(model_name="gpt-4o")
    
    # 2. 노드 등록
    workflow.add_node("summary_node", summary_agent.run)
    workflow.add_node("claim_node", claim_agent.run)
    workflow.add_node("examiner_node", examiner_agent.run)
    workflow.add_node("rewrite_node", rewrite_agent.run)
    
    # 3. 엣지 연결 (직진 코스)
    workflow.add_edge(START, "summary_node")
    workflow.add_edge("summary_node", "claim_node")
    workflow.add_edge("claim_node", "examiner_node") # 1차 초안 작성 후 심사관에게 제출
    
    # 4. 조건부 엣지 (루프 코스)
    workflow.add_conditional_edges(
        "examiner_node",
        should_continue, # 신호등 함수 실행
        {
            "rewrite_node": "rewrite_node", # 빠꾸 먹으면 수정 노드로!
            END: END                        # 통과하면 끝!
        }
    )
    
    # 5. 수정(Rewrite)이 끝나면 다시 심사관에게 제출!
    workflow.add_edge("rewrite_node", "examiner_node")
    
    return workflow.compile()