"""Drawing legacy DB 모듈.

현재 LangGraph MVP에서는 agent 간 데이터 전달에 DB를 사용하지 않고 state를 사용합니다.
이 파일은 기존 DB(GeneratedDrawing 등)와의 하위 호환성을 유지하기 위한 코드로,
drawing_db.py 내부에 있던 DB 관련 클래스와 함수를 분리한 것입니다.

에이전트는 이 모듈을 직접 사용하지 않습니다.
DB 저장이 필요한 경우, Graph나 Master가 agent output을 검증하고 state에 병합한 뒤
외부에서 명시적으로 save_drawings_to_db()를 호출해야 합니다.
"""

from __future__ import annotations


def save_drawings_to_db(user_id: str, consultation_idx: int, drawing_results: list) -> None:
    """도면 결과를 DB에 저장한다. DB 환경에서만 동작한다."""
    from agents.drawing.drawing_db import save_drawings_to_db as _save
    _save(user_id, consultation_idx, drawing_results)


def fetch_drawings_from_db(user_id: str, consultation_idx: int) -> list:
    """DB에서 도면 결과를 조회한다. DB 환경에서만 동작한다."""
    from agents.drawing.drawing_db import fetch_drawings_from_db as _fetch
    return _fetch(user_id, consultation_idx)


__all__ = ["save_drawings_to_db", "fetch_drawings_from_db"]
