# [병합 대상] bizseohyunkim 브랜치의 prior_art_search.py → run() 안의 mock을 교체하세요.
#
# 역할: 발명의 핵심 내용을 바탕으로 유사 선행특허를 검색합니다.
# IPC 코드: G06N, G06F, G06V, G06Q 기준 임베딩 유사도 검색
#
# reads : invention_flow, problem
# writes: similar_patents, ipc_codes

from agents.state import PatentAgentState


def run(state: PatentAgentState) -> dict:
    # ── mock ─────────────────────────────────────────────────────────────────
    return {
        "similar_patents": [
            {
                "id": "KR10-2023-0000001",
                "title": "[MOCK] 유사 특허 1",
                "similarity": 0.91,
                "summary_problem": "[MOCK] 기존 문제점",
                "summary_solution": "[MOCK] 해결 방법",
            }
        ],
        "ipc_codes": ["G06N", "G06F"],
    }
    # ── 실제 구현 위치 ────────────────────────────────────────────────────────
    # from agents.tools.kipris_api import search_by_ipc
    # searcher = PriorArtSearcher()  # bizseohyunkim 브랜치 클래스
    # result = searcher.search(state)
    # return {"similar_patents": result.similar_patents, "ipc_codes": result.ipc_codes}
