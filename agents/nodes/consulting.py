# [병합 대상] consulting 브랜치 → run() 안의 mock을 실제 구현으로 교체하세요.
#
# 역할: 발명가 입력으로부터 발명의 핵심 요소를 추출합니다.
# DB 저장: user_id, session_id, 전체 대화 내역을 별도 저장해야 합니다.
#
# reads : user_input, user_id, session_id, raw_conversation
# writes: is_consultation_done, next_question, raw_conversation,
#         invention_flow, problem, differentiation, effect  ← 상담 완료 시에만

from agents.state import PatentAgentState


def run(state: PatentAgentState) -> dict:
    # ── mock ─────────────────────────────────────────────────────────────────
    history = state.get("raw_conversation") or []
    # user+assistant 메시지 쌍이 3회(=6개) 이상이면 충분한 정보가 모인 것으로 간주.
    # 실제 구현에서는 LLM이 4가지 항목(흐름/문제/차별점/효과) 확보 여부를 판단합니다.
    # 판단 기준: docs/interfaces/consulting.md "상담 종료 판단 기준" 섹션 참조.
    done = len(history) >= 6

    next_q = (
        "[MOCK] 상담이 완료되었습니다. 명세서 작성을 시작합니다." if done
        else "[MOCK] 발명의 효과나 기대 성능을 알려주세요."
    )
    return {
        "is_consultation_done": done,
        "next_question": next_q,
        "invention_flow": f"[MOCK] '{state['user_input']}' 기반 발명 흐름 요약",
        "problem": "[MOCK] 기존 방식의 문제점",
        "differentiation": "[MOCK] 본 발명의 차별점",
        "effect": "[MOCK] 발명의 효과",
        "raw_conversation": [
            {"role": "user", "content": state["user_input"]},
            {"role": "assistant", "content": next_q},
        ],
    }
    # ── 실제 구현 위치 ────────────────────────────────────────────────────────
    # from agents.tools.document_utils import extract_text_from_pdf
    # consultant = PatentConsultant()  # consulting 브랜치 클래스
    # result = consultant.consult(state["user_input"])
    # return {
    #     "invention_flow": result.invention_flow,
    #     "problem": result.problem,
    #     "differentiation": result.differentiation,
    #     "effect": result.effect,
    #     "raw_conversation": result.raw_conversation,
    # }
