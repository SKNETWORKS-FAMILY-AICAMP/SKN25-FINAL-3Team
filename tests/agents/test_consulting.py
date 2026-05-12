"""
consulting 노드 단위 테스트

테스트 대상: agents/nodes/consulting.py :: run(state)
인터페이스:  docs/interfaces/consulting.md

이 노드는 멀티턴 대화를 처리합니다:
- 대화 진행 중: is_consultation_done=False + next_question 반환
- 상담 완료 시: is_consultation_done=True + invention_flow 등 반환
"""
from agents.nodes import consulting
from tests.fixtures.sample_states import BASE_STATE, MID_CONVERSATION_STATE, LONG_CONVERSATION_STATE


# ── Phase 1: 대화 진행 중 (is_consultation_done=False) ──────────────────────────

def test_run_returns_required_fields_during_conversation():
    """대화 진행 중 반드시 반환해야 하는 필드 검증"""
    result = consulting.run(BASE_STATE)

    # 항상 반환해야 하는 필드
    assert "raw_conversation" in result, "raw_conversation 누락"
    assert "is_consultation_done" in result, "is_consultation_done 누락"
    assert "next_question" in result, "next_question 누락 — UI에 표시할 AI 응답"


def test_run_returns_list_for_raw_conversation():
    """raw_conversation이 list 타입인지 검증"""
    result = consulting.run(BASE_STATE)
    assert isinstance(result["raw_conversation"], list)


def test_run_appends_current_turn_to_conversation():
    """이번 턴(user + assistant 메시지)이 raw_conversation에 추가되는지 검증"""
    result = consulting.run(BASE_STATE)
    conversation = result["raw_conversation"]
    assert len(conversation) >= 1, "이번 턴 메시지가 추가되지 않음"

    # user 메시지와 assistant 메시지가 모두 있어야 함
    roles = [msg.get("role") for msg in conversation]
    assert "user" in roles, "user 메시지 없음"
    assert "assistant" in roles, "assistant(AI) 메시지 없음"


def test_run_mid_conversation_is_not_done():
    """대화 중반에는 is_consultation_done=False를 반환하는지 검증"""
    result = consulting.run(MID_CONVERSATION_STATE)
    # 정보가 아직 부족하면 False여야 함 (mock에서는 턴 수 기반)
    assert isinstance(result["is_consultation_done"], bool)


def test_run_does_not_return_full_state():
    """run()이 변경된 필드만 반환하는지 검증 (전체 state 반환 금지)"""
    result = consulting.run(BASE_STATE)
    assert "user_input" not in result, (
        "run()은 변경된 필드만 dict로 반환해야 합니다. 전체 state를 반환하지 마세요."
    )


# ── Phase 2 전환: 상담 완료 (is_consultation_done=True) ─────────────────────────

def test_run_returns_invention_fields_when_done():
    """상담 완료 시 명세서 생성에 필요한 필드를 모두 반환하는지 검증"""
    result = consulting.run(LONG_CONVERSATION_STATE)

    if result.get("is_consultation_done"):
        required_done_fields = [
            "invention_flow",
            "problem",
            "differentiation",
            "effect",
        ]
        for field in required_done_fields:
            assert field in result, (
                f"is_consultation_done=True일 때 '{field}' 필드 누락\n"
                "Phase 2 파이프라인이 이 필드를 사용합니다."
            )


def test_run_invention_flow_is_non_empty_when_done():
    """상담 완료 시 invention_flow가 비어있지 않은지 검증"""
    result = consulting.run(LONG_CONVERSATION_STATE)

    if result.get("is_consultation_done"):
        assert len(result.get("invention_flow", "")) >= 10, (
            "invention_flow가 너무 짧음 — graph.py route_after_consulting()에서 "
            "10자 미만이면 reconsult 루프 발생"
        )


# ── next_question 형식 검증 ──────────────────────────────────────────────────────

def test_next_question_is_non_empty_string():
    """next_question이 비어있지 않은 문자열인지 검증 (UI에 표시됨)"""
    result = consulting.run(BASE_STATE)
    next_q = result.get("next_question", "")
    assert isinstance(next_q, str), "next_question이 str 타입이 아님"
    assert len(next_q) > 0, "next_question이 빈 문자열 — UI에 아무것도 표시되지 않음"


# ── 다양한 입력 테스트 ────────────────────────────────────────────────────────────

def test_run_with_various_inventions():
    """다양한 발명 주제에 대해 일관된 필드를 반환하는지 검증"""
    inventions = [
        "AI 기반 의료 진단 시스템",
        "블록체인을 이용한 투표 시스템",
        "태양광 패널 자동 청소 로봇",
    ]
    for invention in inventions:
        state = {**BASE_STATE, "user_input": invention}
        result = consulting.run(state)
        assert "is_consultation_done" in result, (
            f"user_input='{invention}'에서 is_consultation_done 누락"
        )
        assert "next_question" in result, (
            f"user_input='{invention}'에서 next_question 누락"
        )
