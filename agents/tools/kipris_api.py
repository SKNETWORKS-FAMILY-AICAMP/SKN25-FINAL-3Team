# [구현 필요] KIPRIS 특허 DB 검색 툴
#
# KIPRIS Open API를 활용하여 IPC 코드 기반 특허 검색을 수행합니다.
# https://www.kipris.or.kr/khome/main.do (API 키 발급 필요)
# 주의: 모든 호출은 이 파일을 통해서만 해야 합니다 (CLAUDE.md 규칙 3).


def search_by_ipc(ipc_code: str, keyword: str) -> list[dict]:
    """IPC 코드 + 키워드로 유사 특허를 검색합니다.

    Returns:
        [{"id", "title", "similarity", "summary_problem", "summary_solution"}, ...]
    """
    raise NotImplementedError


def get_patent_detail(patent_id: str) -> dict:
    """특허 번호로 상세 정보를 조회합니다.

    Returns:
        {"id", "title", "claims", "abstract", "ipc_codes", ...}
    """
    raise NotImplementedError
