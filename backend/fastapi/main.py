"""
Patent AI — 멀티에이전트 FastAPI 백엔드

실행:
  uvicorn backend.fastapi.main:app --host 0.0.0.0 --port 8080 --reload

엔드포인트:
  GET  /health
  POST /api/v1/consultation/start
  POST /api/v1/consultation/{session_id}/message
  POST /api/v1/consultation/{session_id}/finalize
  POST /api/v1/pipeline/run
  GET  /api/v1/pipeline/{job_id}/status
  GET  /api/v1/pipeline/{job_id}/result
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.fastapi.routers import consultation, pipeline

app = FastAPI(
    title="Patent AI API",
    version="0.1.0",
    description="특허 상담 및 멀티에이전트 파이프라인 API",
)

# CORS — 프로덕션에서는 allow_origins 를 React 도메인으로 한정할 것
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(consultation.router, prefix="/api/v1/consultation", tags=["consultation"])
app.include_router(pipeline.router,     prefix="/api/v1/pipeline",     tags=["pipeline"])


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
