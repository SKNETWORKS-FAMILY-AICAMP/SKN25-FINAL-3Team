from langgraph.graph import StateGraph, END
from agents.core.state import PatentState
from agents.summary_agent import SummaryAgent
from agents.claim_agent import ClaimGenerationAgent
from agents.examiner_agent import ExaminerAgent

def should_continue(state: PatentState):
    examiner_data = state.get("examiner_data")
    if not examiner_data:
        return END
        
    is_approved = examiner_data.get("is_approved", False)
    revision_count = examiner_data.get("revision_count", 0)
    
    if is_approved or revision_count >= 2:
        return END
    
    return "claim_node"

def build_patent_graph():
    """
    LangGraph Workflow를 조립하고 컴파일합니다.
    """
    workflow = StateGraph(PatentState)

    summary_agent = SummaryAgent(model_name="gpt-4o-mini")
    claim_agent = ClaimGenerationAgent(model_name="gpt-4o")
    
    # RunPod에 배포된 vLLM 엔드포인트 세팅 (주소 및 포트는 환경에 맞게 수정)
    examiner_agent = ExaminerAgent(
        model_name="fine-tuned-examiner-model",
        runpod_base_url="https://api.runpod.ai/v2/<YOUR_POD_ID>/openai/v1", 
        runpod_api_key="<YOUR_RUNPOD_API_KEY>"
    )
    
    # 1. 노드(Node) 등록
    workflow.add_node("summary_node", summary_agent.run)
    workflow.add_node("claim_node", claim_agent.run)
    workflow.add_node("examiner_node", examiner_agent.run)
    
    # 2. 엣지(Edge) 연결
    workflow.set_entry_point("summary_node") 
    workflow.add_edge("summary_node", "claim_node")
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


# mock_data = {
#     "title": "음성 인식 기반 레시피 추천 시스템",
#     "prior_art_problem": "기존 시스템은 재료의 유통기한을 고려하지 않음",
#     "problem_to_solve": "유통기한 임박 재료를 우선 소진하는 레시피 추천",
#     "core_tech": "사용자 음성 입력 -> STT 모듈 -> 유통기한 DB 대조 -> LLM 레시피 생성",
#     "expected_effect": "음식물 쓰레기 감소 및 사용자 편의성 증대"
# }

# # Graph 실행 예시
# # app = build_patent_graph()
# # result = app.invoke({"mock_input_data": mock_data})