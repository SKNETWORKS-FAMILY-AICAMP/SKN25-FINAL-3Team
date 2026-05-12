import httpx
from django.conf import settings

_BASE = settings.AGENT_API_BASE_URL


async def consult(user_input: str, user_id: str, session_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{_BASE}/consult", json={
            "user_input": user_input,
            "user_id": user_id,
            "session_id": session_id,
        })
        r.raise_for_status()
        return r.json()


async def run_full_pipeline(user_input: str, user_id: str, session_id: str) -> dict:
    """상담부터 명세서 작성까지 전체 파이프라인을 순차 호출합니다.

    TODO: 현재는 /consult 1회 호출 후 바로 Phase 2로 진행합니다.
    실제 구현에서는 is_consultation_done=True가 될 때까지 /consult를 반복
    호출하는 멀티턴 루프로 교체해야 합니다.
    Django View 레벨에서 세션 상태를 관리하며 루프를 처리하는 방식을 권장합니다.
    상세: docs/decisions/003-multiturn-session.md
    """
    consultation = await consult(user_input, user_id, session_id)

    async with httpx.AsyncClient(timeout=60.0) as client:
        claims_r = await client.post(f"{_BASE}/claims", json=consultation)
        claims_r.raise_for_status()
        claims = claims_r.json()

        examiner_r = await client.post(f"{_BASE}/examine", json=claims)
        examiner_r.raise_for_status()

        drawing_r = await client.post(f"{_BASE}/drawing", json=claims)
        drawing_r.raise_for_status()
        drawing = drawing_r.json()

        description_r = await client.post(f"{_BASE}/description", json={
            **consultation,
            **drawing,
        })
        description_r.raise_for_status()

    return {
        "consultation": consultation,
        "claims": claims,
        "drawing": drawing,
        "description": description_r.json(),
    }
