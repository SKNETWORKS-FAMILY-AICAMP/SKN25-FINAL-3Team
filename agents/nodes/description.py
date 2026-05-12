# [구현 필요] 담당자 미배정 — run() 안의 mock을 교체하세요.
#
# 역할: 발명의 핵심 내용 + 도면을 바탕으로 발명의 상세한 설명을 작성합니다.
# 출력 목차: 배경기술 / 해결하려는 과제 / 과제의 해결수단 / 발명의 효과
#            도면의 간단한 설명 / 발명을 실시하기 위한 구체적인 내용 (실시예)
#
# reads : invention_flow, problem, differentiation, effect, flowchart_code, system_diagram_code
# writes: background, problem_statement, solution, drawing_description, detailed_description

from agents.state import PatentAgentState


def run(state: PatentAgentState) -> dict:
    # ── mock ─────────────────────────────────────────────────────────────────
    return {
        "background": f"[MOCK] 배경기술: {state['problem']}",
        "problem_statement": f"[MOCK] 해결하려는 과제: {state['problem']}",
        "solution": f"[MOCK] 과제의 해결수단: {state['differentiation']}",
        "drawing_description": "[MOCK] 도 1은 본 발명의 흐름도이다.",
        "detailed_description": f"[MOCK] 실시예: {state['invention_flow']}",
    }
