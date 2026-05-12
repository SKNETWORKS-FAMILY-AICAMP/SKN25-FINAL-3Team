# [구현 필요] feature/esc-claim 브랜치에서 작업 후 run() 안의 mock을 교체하세요.
#
# 역할: 청구항이 특허법·심사기준에 부합하는지 검토합니다.
# 파인튜닝 데이터: KIPRIS 의견제출통지서, 거절결정통지서, 등록결정서
#
# reads : claims
# writes: is_registerable, examiner_opinion, examiner_issues
# 이후 흐름: graph.py route_after_examiner()가 is_registerable 값을 보고
#            True  → drawing 노드로 진행
#            False → claims 노드로 돌아가 재작성 (최대 MAX_REVISION=2회)

from agents.state import PatentAgentState


def run(state: PatentAgentState) -> dict:
    # ── mock ─────────────────────────────────────────────────────────────────
    return {
        "is_registerable": True,
        "examiner_opinion": "[MOCK] 청구항이 신규성·진보성 요건을 충족합니다.",
        "examiner_issues": [],
    }
