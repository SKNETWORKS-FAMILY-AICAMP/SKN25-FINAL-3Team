"""특허 agent service의 FastAPI 진입점입니다.

─ 등록된 API 경로 ─
  POST /api/pipeline/run          : 전체 파이프라인 새로 실행
  POST /api/pipeline/continue     : 기존 파이프라인 이어서 실행
  POST /api/agents/{name}/run     : 특정 agent 하나만 실행
  GET  /api/runs/{run_id}         : 실행 상태/결과 조회
  GET  /health                    : 서버 상태 확인

─ 시작 시 ─
  DB 마이그레이션은 컨테이너 entrypoint에서 alembic upgrade head 로 처리합니다.
  .env 파일을 로드합니다 (로컬 uvicorn 실행 시).
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# load_dotenv(): .env 파일을 읽어 환경변수로 등록합니다.
# Docker 환경에서는 env_file 설정으로 이미 들어오므로 중복 호출은 무해합니다.
load_dotenv()

from backend.fastapi.app.routers import agents as agents_router
from backend.fastapi.app.routers.pipeline import router as pipeline_router
from backend.fastapi.app.routers.runs import router as runs_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    # 테이블 생성은 alembic upgrade head 로 처리합니다.
    yield


app = FastAPI(title="Patent AI Agent Service", version="0.1.0", lifespan=lifespan)


# ── CORS 미들웨어 ──────────────────────────────────────
# 브라우저에서 React 앱이 이 API를 호출할 때 필요한 보안 허용 설정입니다.
# main 반영용 PR에서는 기존 동작과 비슷하게 기본값을 "*"로 둡니다.
# 배포 시에는 CORS_ORIGINS=https://frontend.example.com 처럼 실제 프론트 도메인으로 제한하세요.
_raw_cors_origins = os.getenv("CORS_ORIGINS", "*")
cors_origins = [origin.strip() for origin in _raw_cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if "*" in cors_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── router 등록 ─────────────────────────────────────────
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(agents_router.router, prefix="/api/agents", tags=["agents"])
app.include_router(runs_router, prefix="/api/runs", tags=["runs"])


@app.get("/health")
def health() -> dict[str, str]:
    """배포/테스트용 헬스체크입니다."""
    return {"status": "ok", "service": "patent-agent"}
