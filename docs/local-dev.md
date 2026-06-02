# 로컬 개발 가이드 (Docker 없이)

Docker Compose 없이 서비스를 직접 실행해 빠르게 반복 개발하는 방법입니다.

## 사전 요구사항

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` 또는 공식 설치 스크립트)
- PostgreSQL 15+ (`pgvector` 확장 포함) — 아래 중 하나:
  - 로컬 설치: `brew install postgresql@15` (macOS)
  - 또는 postgres만 Docker로 띄우기 (권장): `docker compose up -d postgres redis`
- Node.js 20+ (프론트엔드 작업 시)

---

## 1. 환경변수 설정

```bash
cp .env.example .env
```

`.env`에서 최소한 아래 값을 채웁니다:

```dotenv
OPENAI_API_KEY=sk-...

# 로컬 postgres를 직접 쓴다면
DATABASE_URL=postgresql://patent:patent_pw@localhost:5432/patent_ai
DJANGO_DB_HOST=localhost
DJANGO_DB_PASSWORD=patent_pw

# Redis를 직접 쓴다면
REDIS_URL=redis://localhost:6379/0
```

postgres와 redis만 Docker로 띄우는 경우:

```bash
docker compose up -d postgres redis
```

---

## 2. 의존성 설치

### FastAPI + 에이전트 개발

```bash
uv sync --group shared --group fastapi --group dev
```

### Django 개발

```bash
uv sync --group shared --group django --group dev
```

### 전체 설치 (두 서비스 모두)

```bash
uv sync --group shared --group fastapi --group django --group dev
```

---

## 3. FastAPI 서버 실행

프로젝트 루트에서 실행합니다 (`alembic.ini`가 루트에 있습니다).

```bash
# DB 마이그레이션 (최초 1회, DB 스키마 변경 후)
uv run alembic upgrade head

# 개발 서버 실행 (--reload: 코드 변경 자동 반영)
uv run uvicorn backend.fastapi.app.main:app --host 0.0.0.0 --port 8080 --reload
```

확인:

```bash
curl http://localhost:8080/health
# → {"status":"ok"}

# Swagger UI
open http://localhost:8080/docs
```

---

## 4. Django 서버 실행

```bash
cd backend/django

uv run python manage.py migrate --noinput
uv run python manage.py runserver 0.0.0.0:8000
```

확인:

```bash
curl http://localhost:8000/api/auth/me/
# → {"detail":"Authentication credentials were not provided."}  (401 정상)
```

---

## 5. 테스트 실행

LLM·DB·Redis 연결 없이 실행되는 단위 테스트입니다. 프로젝트 루트에서 실행합니다.

```bash
# 전체 테스트
uv run pytest

# 특정 경로만
uv run pytest tests/agents/
uv run pytest tests/api/

# 상세 출력
uv run pytest -v

# 특정 테스트만
uv run pytest tests/agents/test_master.py -v
```

---

## 6. 린트·포맷

```bash
# 검사
uv run ruff check .

# 자동 수정
uv run ruff check --fix .
```

---

## 7. Alembic 마이그레이션 관리

```bash
# 현재 리비전 확인
uv run alembic current

# 새 마이그레이션 생성
uv run alembic revision --autogenerate -m "add_new_table"

# 특정 리비전으로 롤백
uv run alembic downgrade -1
```

---

## 8. 프론트엔드 개발 서버

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Vite 프록시 설정 (`frontend/vite.config.ts`):
- `/api/*` → `http://localhost:8080` (FastAPI)
- `/auth/*` → `http://localhost:8000` (Django)

FastAPI와 Django가 각각 8080, 8000에서 실행 중이어야 합니다.

---

## 포트 요약

| 서비스 | 로컬 포트 | 용도 |
|--------|-----------|------|
| Frontend | 3000 | React 개발 서버 |
| Django | 8000 | JWT 인증 API |
| FastAPI | 8080 | 파이프라인 API + Swagger |
| PostgreSQL | 5432 | 공유 DB |
| Redis | 6379 | 파이프라인 진행상황 |
