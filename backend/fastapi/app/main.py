"""특허 agent service의 FastAPI 진입점입니다.

─ FastAPI란? ─
  Python으로 REST API를 만드는 프레임워크입니다.
  @app.get("/health") 같은 데코레이터로 URL 경로와 함수를 연결합니다.

─ 이 파일의 역할 ─
  1. FastAPI 앱 객체 생성
  2. CORS 미들웨어 설정 (브라우저 보안 정책 허용)
  3. router 등록 (pipeline, agents)
  4. 헬스체크 엔드포인트

─ 등록된 API 경로 ─
  POST /api/pipeline/run      : 전체 파이프라인 새로 실행
  POST /api/pipeline/continue : 기존 파이프라인 이어서 실행
  POST /api/agents/{name}/run : 특정 agent 하나만 실행
  GET  /health                : 서버 상태 확인

─ 프론트엔드는 개별 agent를 직접 호출하지 않습니다 ─
  /api/pipeline/* 또는 /api/agents/* 경유로만 접근합니다.
  실제 orchestration은 agents.master.router와 agents.graph가 담당합니다.
"""
from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# load_dotenv(): 프로젝트 루트의 .env 파일을 읽어 환경변수로 등록합니다.
# Docker 환경에서는 env_file 설정으로 이미 환경변수가 들어오므로 중복 호출은 무해합니다.
# 로컬에서 uvicorn으로 직접 실행할 때 OPENAI_API_KEY 등이 로드됩니다.
load_dotenv()

from backend.fastapi.app.routers import agents as agents_router
from backend.fastapi.app.routers.pipeline import router as pipeline_router

app = FastAPI(title="Patent AI Agent Service", version="0.1.0")

# ── CORS 미들웨어 ──────────────────────────────────
# CORS(Cross-Origin Resource Sharing)란?
# 브라우저가 "다른 출처(origin)의 서버에 요청을 보낼 때"에 적용하는 보안 정책입니다.
# 예: React 앱이 localhost:3000에서 실행되고, 이 API는 localhost:8000에 있을 때,
#     브라우저는 "두 곳의 포트가 다르므로 다른 출처"라고 판단해서 요청을 차단합니다.
# CORSMiddleware를 추가하면 서버가 "이 요청은 허용한다"는 응답 헤더를 붙여줍니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # "*"는 모든 출처 허용. 배포 시 실제 도메인으로 교체하세요.
                             # 예: ["https://myapp.com", "http://localhost:3000"]
    allow_credentials=True,  # 쿠키/인증 헤더 포함 요청 허용
    allow_methods=["*"],     # GET, POST, PUT, DELETE 등 모든 HTTP 메서드 허용
    allow_headers=["*"],     # 모든 요청 헤더 허용
)

# ── router 등록 ─────────────────────────────────────
# APIRouter: URL 경로를 그룹으로 묶는 FastAPI의 기능입니다.
# prefix로 공통 경로를 붙이고, tags로 API 문서(/docs)에서 그룹 이름을 표시합니다.
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(agents_router.router, prefix="/api/agents", tags=["agents"])


@app.get("/health")
def health() -> dict[str, str]:
    """배포/테스트용 헬스체크입니다.

    Docker의 HEALTHCHECK와 로드밸런서가 이 경로를 주기적으로 호출해서
    서버가 정상적으로 동작하는지 확인합니다.
    """
    return {"status": "ok", "service": "patent-agent"}
