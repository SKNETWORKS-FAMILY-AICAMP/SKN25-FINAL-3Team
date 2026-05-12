# [구현 필요] claim 브랜치에서 작업 후 run() 안의 mock을 교체하세요.
#
# 역할: 발명의 핵심 내용을 바탕으로 독립항·종속항을 작성합니다.
# 출력: 방법/시스템/기록매체 청구항 포함, 권리범위 최대화 목표
#
# reads : invention_flow, differentiation, effect, revision_count
# writes: claims, revision_count
# 주의: examiner가 "revise"를 반환하면 이 노드가 재호출됩니다.
#       revision_count를 여기서 +1하여 graph.py MAX_REVISION 초과 여부를 추적합니다.

from agents.state import PatentAgentState


def run(state: PatentAgentState) -> dict:
    # ── mock ─────────────────────────────────────────────────────────────────
    return {
        "revision_count": state.get("revision_count", 0) + 1,  # 재작성 횟수 누적
        "claims": [
            {
                "claim_number": 1,
                "claim_type": "method",
                "is_independent": True,
                "depends_on": 0,
                "content": f"[MOCK] {state['invention_flow']}에 기반한 방법 청구항",
            },
            {
                "claim_number": 2,
                "claim_type": "system",
                "is_independent": True,
                "depends_on": 0,
                "content": "[MOCK] 시스템 청구항",
            },
            {
                "claim_number": 3,
                "claim_type": "method",
                "is_independent": False,
                "depends_on": 1,
                "content": "[MOCK] 제1항에 있어서, 종속 청구항",
            },
        ]
    }
