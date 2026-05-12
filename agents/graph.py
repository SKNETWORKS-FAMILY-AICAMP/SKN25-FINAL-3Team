from langgraph.graph import StateGraph, END
from agents.state import PatentAgentState
from agents.nodes import consulting, patent_search, claims, examiner, drawing, description

MAX_REVISION = 2  # 청구항 재작성 최대 횟수


def route_after_consulting(state: PatentAgentState) -> str:
    """
    상담(consulting) 단계 이후 is_consultation_done 값에 따라 분기합니다.

    - True  → Phase 2(patent_search / claims)로 진행
    - False → consulting 루프 유지(재질문)
    """
    if state.get("is_consultation_done"):
        return "proceed"
    return "reconsult"


# ─────────────────────────────────────────────────────────────────────────────
# 조건부 엣지(Conditional Edge) 란?
#
# add_conditional_edges(source, router_fn, path_map) 형태로 사용합니다.
# router_fn 이 문자열 키를 반환하면, path_map 에서 다음 노드를 찾아 이동합니다.
# 조건에 따라 다른 노드로 분기하거나 루프를 만들 때 사용합니다.
#
# 주의: 동일 노드에 add_conditional_edges 와 add_edge 를 함께 사용하면
#       조건과 무관하게 두 경로 모두 실행됩니다 (fan-out).
#       분기가 필요한 경우 add_conditional_edges 만 사용하세요.
# ─────────────────────────────────────────────────────────────────────────────

def route_after_examiner(state: PatentAgentState) -> str:
    """
    Examiner Agent 결과에 따라 분기합니다.

    - 등록 가능 → Drawing Agent 진행
    - 등록 불가 + 재시도 횟수 미달 → Claims Agent 로 돌아가 재작성
    - 등록 불가 + 재시도 횟수 초과 → 그대로 Drawing Agent 진행 (최선의 결과 사용)
    """
    if state.get("is_registerable"):
        return "approved"

    if state.get("revision_count", 0) < MAX_REVISION:
        return "revise"

    return "approved"  # 최대 재시도 초과 → 강제 통과


def build_graph() -> StateGraph:
    graph = StateGraph(PatentAgentState)

    graph.add_node("consulting",    consulting.run)
    graph.add_node("patent_search", patent_search.run)
    graph.add_node("claims",        claims.run)
    graph.add_node("examiner",      examiner.run)
    graph.add_node("drawing",       drawing.run)
    graph.add_node("description",   description.run)

    graph.set_entry_point("consulting")

    # ── consulting → Phase 2 진입 ─────────────────────────────────────────────
    # TODO: 현재는 항상 Phase 2로 직행합니다. 멀티턴 루프가 미구현 상태입니다.
    #
    # 목표 동작: is_consultation_done=False이면 consulting으로 돌아와 재질문해야 합니다.
    # route_after_consulting() 함수가 이미 준비되어 있지만 아직 그래프에 연결되지 않았습니다.
    #
    # 구현 시 아래 두 add_edge를 삭제하고 add_conditional_edges로 교체하세요:
    #   graph.add_conditional_edges(
    #       "consulting",
    #       route_after_consulting,
    #       {
    #           "proceed":   ["patent_search", "claims"],  # 병렬 fan-out
    #           "reconsult": "consulting",                 # 루프백
    #       },
    #   )
    # 주의: LangGraph에서 conditional → 복수 노드 fan-out은 버전별 지원 방식이 다릅니다.
    #       docs/decisions/003-multiturn-session.md 참조.
    graph.add_edge("consulting", "patent_search")
    graph.add_edge("consulting", "claims")

    # ── 청구항 파이프라인 ─────────────────────────────────────────────────────
    graph.add_edge("claims", "examiner")

    # ── 조건부 엣지: examiner 결과에 따라 재작성 루프 ────────────────────────
    graph.add_conditional_edges(
        "examiner",
        route_after_examiner,
        {
            "approved": "drawing",  # 등록 가능 → 도면 작성
            "revise":   "claims",   # 등록 불가 → 청구항 재작성 (revision_count 증가)
        },
    )

    # ── 나머지 엣지 ──────────────────────────────────────────────────────────
    graph.add_edge("drawing",       "description")
    graph.add_edge("description",   END)
    graph.add_edge("patent_search", END)

    return graph.compile()


patent_graph = build_graph()
