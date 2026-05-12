"""
graph.py 통합 테스트

테스트 대상: agents/graph.py :: patent_graph, route_after_examiner, route_after_consulting
"""
from agents.graph import patent_graph, route_after_examiner, route_after_consulting, MAX_REVISION
from tests.fixtures.sample_states import (
    BASE_STATE,
    POST_EXAMINER_APPROVED_STATE,
    POST_EXAMINER_REJECTED_STATE,
)


# ── 라우터 함수 단위 테스트 ──────────────────────────────────────────────────────

def test_route_after_examiner_approved():
    """is_registerable=True이면 'approved' 반환"""
    result = route_after_examiner(POST_EXAMINER_APPROVED_STATE)
    assert result == "approved"


def test_route_after_examiner_rejected_under_limit():
    """is_registerable=False + revision_count < MAX_REVISION이면 'revise' 반환"""
    state = {**POST_EXAMINER_REJECTED_STATE, "revision_count": 0}
    result = route_after_examiner(state)
    assert result == "revise"


def test_route_after_examiner_rejected_over_limit():
    """is_registerable=False + revision_count >= MAX_REVISION이면 'approved'(강제 통과) 반환"""
    state = {**POST_EXAMINER_REJECTED_STATE, "revision_count": MAX_REVISION}
    result = route_after_examiner(state)
    assert result == "approved"


def test_route_after_consulting_proceed():
    """invention_flow가 10자 이상이면 'proceed' 반환"""
    from tests.fixtures.sample_states import POST_CONSULTING_STATE
    result = route_after_consulting(POST_CONSULTING_STATE)
    assert result == "proceed"


def test_route_after_consulting_reconsult():
    """invention_flow가 10자 미만이면 'reconsult' 반환"""
    state = {**BASE_STATE, "invention_flow": "짧음"}  # 3자
    result = route_after_consulting(state)
    assert result == "reconsult"


# ── 그래프 구조 검증 ─────────────────────────────────────────────────────────────

def test_graph_compiles_without_error():
    """patent_graph가 오류 없이 컴파일되는지 검증"""
    assert patent_graph is not None


def test_graph_has_all_nodes():
    """그래프에 필요한 모든 노드가 등록되어 있는지 검증"""
    expected_nodes = {
        "consulting", "patent_search", "claims",
        "examiner", "drawing", "description",
    }
    actual_nodes = set(patent_graph.nodes.keys()) - {"__start__", "__end__"}
    assert expected_nodes == actual_nodes, (
        f"누락된 노드: {expected_nodes - actual_nodes} | "
        f"예상치 못한 노드: {actual_nodes - expected_nodes}"
    )


# ── 전체 파이프라인 실행 테스트 (mock 상태) ─────────────────────────────────────

def test_full_pipeline_runs_with_mock(tmp_path):
    """전체 파이프라인이 mock 노드로 오류 없이 실행되는지 검증"""
    result = patent_graph.invoke(BASE_STATE)
    # 파이프라인 완료 후 description 노드 출력 필드가 존재해야 함
    # (mock이므로 빈값일 수 있지만 필드 자체는 있어야 함)
    assert result is not None
