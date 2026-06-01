"""특허 agent service의 FastAPI 진입점입니다.

프론트엔드는 개별 agent를 직접 호출하지 않고 이 앱의 pipeline API를 호출합니다.
실제 orchestration은 agents.master.router와 agents.graph가 담당합니다.
"""
from __future__ import annotations

from fastapi import FastAPI

from backend.fastapi.app.routers.pipeline import router as pipeline_router

app = FastAPI(title="Patent AI Agent Service", version="0.1.0")
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["pipeline"])


@app.get("/health")
def health() -> dict[str, str]:
    """배포/테스트용 헬스체크입니다."""
    return {"status": "ok", "service": "patent-agent"}
