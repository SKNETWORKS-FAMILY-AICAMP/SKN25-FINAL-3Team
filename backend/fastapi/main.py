# backend/fastapi/main.py
import os
import sys
import django
from fastapi import FastAPI

sys.path.insert(0, os.path.join(os.getcwd(), 'backend', 'django'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from backend.fastapi.routers import claims, drawings, specification

app = FastAPI(
    title="Patent AI Worker", 
    description="특허 생성 AI 워커 FastAPI 서버",
    version="1.0.0"
)

app.include_router(claims.router, prefix="/api/v1", tags=["Claims & Prior Art"])
app.include_router(drawings.router, prefix="/api/v1", tags=["Drawings"])
app.include_router(specification.router, prefix="/api/v1", tags=["Specification"])

# 서버 구동 시 안내 메시지 (디버깅용)
@app.on_event("startup")
async def startup_event():
    print("🚀 FastAPI AI Worker 가동 완료! (Django 세팅 로드 성공)")

@app.get("/health")
def health_check():
    return {"status": "ok"}