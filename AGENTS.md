# AGENTS.md — Patent AI Agent Service

AI 코딩 어시스턴트를 위한 프로젝트 가이드입니다.
코드 작업 전 이 파일을 읽고, 세부 내용은 아래 링크된 문서를 참조하세요.

---

## 프로젝트 개요

발명 아이디어를 입력받아 특허 초안(청구항·도면·명세서)을 자동 생성하는 멀티에이전트 서비스입니다.

```
Browser (React :3000)
  ├── /api/*  → FastAPI :8080  — 파이프라인 + 비즈니스 로직
  └── /auth/* → Django  :8000  — JWT 인증 전용
                    ↓
              PostgreSQL :5432  (공유 DB, pgvector)
              Redis      :6379  (파이프라인 진행상황)
```

---

## 디렉터리 구조

```
agents/               멀티에이전트 파이프라인 핵심 로직
  schemas/            Agent별 Pydantic output 계약
  adapters/           state ↔ agent 변환 계층 (base.py)
  {name}/             각 agent 구현 (adapter.py + *_agent.py)
  graph.py            파이프라인 실행 흐름
  state.py            공유 state 컨테이너 (PatentAgentState)
  validation.py       output 검증 + LLM repair
  repair.py           형식 교정 전용 LLM repair

backend/
  django/             JWT 인증 서비스 (manage.py, config/)
  fastapi/app/        FastAPI 진입점 + routers/

frontend/             React + TypeScript (Vite)
  src/api/            API 클라이언트
  src/                컴포넌트·페이지

docker/               Dockerfile.*  (django, fastapi, frontend, claim)
docs/                 설계 문서 (아래 참조)
tests/                단위 테스트 (agents/, api/)
```

---

## 영역별 핵심 규칙

### Agent 파이프라인 (`agents/`)

- 새 agent 추가 시 반드시 **schema → adapter → graph 등록** 순서로 구현합니다.
  - `agents/schemas/{name}.py` — `AgentOutputBase` 상속 Pydantic 모델
  - `agents/{name}/adapter.py` — `AgentAdapter` 상속, `state_key` 지정
  - `agents/graph.py` — `build_default_adapters()`에 등록
- agent output을 state에 직접 쓰지 않습니다. adapter와 `safe_validate_output()`을 거칩니다.
- 검증 실패 시 `AgentValidationError`가 발생합니다. 조용히 무시하거나 fallback으로 우회하지 않습니다.
- 후속 agent는 `state["summary"]["structured_invention"]`을 공통 입력으로 읽습니다.

→ 상세: [docs/architecture/agent_contracts.md](docs/architecture/agent_contracts.md)

### FastAPI (`backend/fastapi/`)

- DB 마이그레이션은 `alembic upgrade head`로 처리합니다 (컨테이너 기동 시 자동 실행).
- 새 라우터는 `backend/fastapi/app/routers/`에 추가하고 `main.py`에서 `include_router`합니다.
- `GET /health`는 건드리지 않습니다 (Docker healthcheck가 의존).

### Django (`backend/django/`)

- 인증(`/api/auth/*`) 외의 비즈니스 로직을 추가하지 않습니다.
- 마이그레이션은 `python manage.py migrate`로 관리합니다 (Alembic과 독립).

### Frontend (`frontend/`)

- API 호출은 `/api/*` (→ FastAPI), 인증은 `/auth/*` (→ Django)로 라우팅합니다. 직접 포트를 하드코딩하지 않습니다.
- 프록시 설정은 `frontend/vite.config.ts`를 참조합니다.

### 테스트 (`tests/`)

- 단위 테스트는 LLM·DB·Redis 연결 없이 실행되어야 합니다.
- `uv run pytest`로 전체 실행합니다.

---

## 참고 문서

| 문서 | 내용 |
|------|------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Docker Compose 전체 스택 실행 및 확인 |
| [docs/local-dev.md](docs/local-dev.md) | Docker 없이 로컬 실행 (uv, alembic, pytest) |
| [docs/architecture/agent_contracts.md](docs/architecture/agent_contracts.md) | Agent 입출력 계약, schema 상세, state 구조 |
| [docs/architecture/deployment_topology.md](docs/architecture/deployment_topology.md) | 배포 구조, 서비스 경계, storage lifecycle |
| [docs/adr/](docs/adr/) | 주요 설계 의사결정 기록 |
| [BRANCH_RULES.md](BRANCH_RULES.md) | 브랜치 규칙, PR 체크리스트 |
