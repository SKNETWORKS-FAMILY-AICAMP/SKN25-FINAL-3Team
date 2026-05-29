# graph.py
from langgraph.graph import StateGraph, START, END
from state import PatentState

# 각 에이전트 클래스 임포트
from summary import SummaryAgent
from claim import ClaimAgent
from examiner import ExaminerAgent
from claim_rewrite import ClaimRewriteAgent
from drawing import SmartDrawingAgent

# =========================================================
# 1. 에이전트 인스턴스 초기화
# =========================================================
summary_agent = SummaryAgent()
claim_agent = ClaimAgent()
examiner_agent = ExaminerAgent()
rewrite_agent = ClaimRewriteAgent()
drawing_agent = SmartDrawingAgent()

# =========================================================
# 2. 노드(Node) 함수 정의
# =========================================================
def summary_node(state: PatentState):
    return summary_agent.run(state)

def drawing_node(state: PatentState):
    return drawing_agent.run(state)

def claim_node(state: PatentState):
    return claim_agent.run(state)

def examiner_node(state: PatentState):
    return examiner_agent.run(state)

def claim_rewrite_node(state: PatentState):
    return rewrite_agent.run(state)

# =========================================================
# 3. 조건부 라우팅(Conditional Edge) 함수 정의
# =========================================================
def should_rewrite(state: PatentState):
    """
    심사관의 결과를 확인하고 다음 경로를 결정합니다.
    """
    examiner_data = state.get("examiner_data")
    
    # 승인되었으면 끝, 아니면 보정(rewrite)으로 이동
    if examiner_data and examiner_data.is_approved:
        return "end"
    else:
        return "rewrite"

def after_rewrite(state: PatentState):
    """
    청구항 재작성 후, 재심사를 받을지 종료할지 결정합니다.
    (최대 2회 재작성 제한)
    """
    examiner_data = state.get("examiner_data")
    
    # examiner_data.revision_count는 심사관 에이전트가 실행될 때마다 1씩 증가합니다.
    # 2번 거절당하고 2번째 재작성을 마쳤다면 무조건 종료
    if examiner_data and examiner_data.revision_count >= 2:
        return "end"
    else:
        return "examiner"

# =========================================================
# 4. 그래프(Graph) 조립
# =========================================================
workflow = StateGraph(PatentState)

# 노드 추가
workflow.add_node("summary", summary_node)
workflow.add_node("drawing", drawing_node)
workflow.add_node("claim", claim_node)
workflow.add_node("examiner", examiner_node)
workflow.add_node("claim_rewrite", claim_rewrite_node)

# 엣지 연결 (흐름 정의)
workflow.add_edge(START, "summary")

# [병렬 처리] summary 이후 drawing과 claim이 동시에 실행됨
workflow.add_edge("summary", "drawing")
workflow.add_edge("summary", "claim")

# drawing은 끝나면 종료 (독립적인 산출물)
workflow.add_edge("drawing", END)

# claim이 끝나면 심사관에게 전달
workflow.add_edge("claim", "examiner")

# 심사관 결과에 따른 조건부 분기 (승인 -> 종료 / 거절 -> 보정)
workflow.add_conditional_edges(
    "examiner",
    should_rewrite,
    {
        "end": END,
        "rewrite": "claim_rewrite"
    }
)

# 보정(rewrite) 후 조건부 분기 (최대 2회 왕복 후 종료)
workflow.add_conditional_edges(
    "claim_rewrite",
    after_rewrite,
    {
        "examiner": "examiner",
        "end": END
    }
)

# =========================================================
# 5. 그래프 컴파일
# =========================================================
app = workflow.compile()