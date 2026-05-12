# [병합 대상] bizseohyunkim 브랜치의 drawing_agent.py, claim_to_flowchart.py
#
# 역할: 청구항을 바탕으로 mermaid.js 도면을 생성합니다.
#
# reads : claims
# writes: flowchart_code, system_diagram_code

from agents.state import PatentAgentState


def run(state: PatentAgentState) -> dict:
    # ── mock ─────────────────────────────────────────────────────────────────
    claim_count = len(state.get("claims", []))
    return {
        "flowchart_code": f"flowchart TD\n    A[발명 시작] --> B[처리 단계]\n    B --> C[결과]\n    %% 청구항 {claim_count}개 기반",
        "system_diagram_code": "flowchart LR\n    User --> System --> DB",
    }
