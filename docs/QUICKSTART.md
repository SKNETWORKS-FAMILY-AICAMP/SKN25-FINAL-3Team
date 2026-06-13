# Quickstart — Patent AI Agent Service

## 사전 준비

- Docker Desktop (또는 Docker Engine + Compose v2)
- `.env` 파일 (아래 내용으로 프로젝트 루트에 생성)

```dotenv
# 필수
OPENAI_API_KEY=sk-...

# Critic Agent (AWS vLLM) — 설정하지 않으면 Examiner Agent 실행 시 오류
RUNPOD_VLLM_URL=http://<aws-instance-ip>:8000/v1
RUNPOD_API_KEY=<발급받은_api_key>

# 선택 (기본값으로 동작)
OPENAI_MODEL=gpt-4o
OPENAI_CHAT_MODEL=gpt-4o-mini
DB_USER=patent
DB_PASSWORD=patent_pw
DB_NAME=patent_ai
SECRET_KEY=django-insecure-change-this-in-production-key-12345
```

---

## 실행

### 기본 스택 (GPU 불필요)

```bash
docker compose up --build
```

모든 컨테이너가 `healthy` 상태가 될 때까지 1-2분 대기합니다.

### Critic Agent 연동 (외부 AWS vLLM)

Critic Agent(심사관 교차검증)는 AWS에서 vLLM으로 서빙되는 외부 LLM에 연결합니다.
로컬 GPU나 `--profile llm` 없이 `.env`에 아래 두 값만 추가하면 됩니다.

```dotenv
# Critic Agent — AWS vLLM 엔드포인트 (OpenAI 호환)
RUNPOD_VLLM_URL=http://<aws-instance-ip>:8000/v1
RUNPOD_API_KEY=<발급받은_api_key>
```

설정 후 기본 스택을 그대로 올리면 Examiner Agent가 자동으로 해당 엔드포인트를 사용합니다.

```bash
docker compose up --build
```

> `RUNPOD_VLLM_URL`을 설정하지 않으면 Examiner Agent 실행 시 연결 오류가 발생합니다.

### 특허 코퍼스 DB 적재 (최초 1회)

```bash
docker compose run --rm fastapi \
  python agents/priorart/load_corpus.py
```

상세 옵션 및 환경변수 설정은 [docs/corpus-loading.md](corpus-loading.md)를 참조하세요.

### 컨테이너 개별 실행

전체 스택 대신 특정 컨테이너만 올릴 때 사용합니다.  
`depends_on` 설정에 따라 의존 서비스는 자동으로 함께 기동됩니다.

```bash
# 인프라 (DB + 캐시)
docker compose up postgres          # postgres만
docker compose up redis             # redis만
docker compose up postgres redis    # 인프라 두 개만

# 인증 서버 — postgres가 자동으로 함께 기동됩니다
docker compose up django

# API 서버 — postgres + redis가 자동으로 함께 기동됩니다
docker compose up fastapi

# 프론트엔드 — fastapi + django(+ 각 의존 서비스)가 자동으로 함께 기동됩니다
docker compose up frontend

# Critic Agent (GPU 필요, --profile llm 필수)
docker compose --profile llm up claim-api
```

빌드가 필요한 경우 `--build` 플래그를 추가하세요.

```bash
docker compose up --build django
docker compose up --build fastapi
```

백그라운드로 실행하려면 `-d` 플래그를 사용하세요.

```bash
docker compose up -d postgres redis
docker compose up -d django fastapi
```

---

## 컨테이너별 확인 방법

### 1. postgres `:5432` — 공유 데이터베이스 (pgvector)

```bash
docker compose exec postgres pg_isready -U patent -d patent_ai
# → patent_ai:5432 - accepting connections
```

> Django 인증 테이블, 파이프라인 실행 기록, 특허 벡터 임베딩(1536-dim)을 모두 보관합니다.

---

### 2. redis `:6379` — 파이프라인 진행상황 추적

```bash
docker compose exec redis redis-cli ping
# → PONG
```

> `run:{run_id}:agent` 키에 현재 실행 중인 에이전트 이름이 TTL 1일로 저장됩니다.

---

### 3. django `:8000` — 인증 + 워크스페이스 UI

```bash
curl -s http://localhost:8000/health/
# → {"status":"ok","service":"patent-auth"}
```

브라우저에서 http://localhost:8000 접속 시 로그인 페이지로 이동합니다.  
로그인 후 `/workspace/dashboard/` 에서 특허 프로젝트를 관리할 수 있습니다.

**JWT REST API 엔드포인트** (React 프론트엔드 또는 FastAPI 연동용)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/auth/signup/` | 회원가입 (`username`, `name`, `gender`, `age`, `password`, `password2`) |
| POST | `/api/auth/login/` | 로그인 → access/refresh 토큰 반환 |
| POST | `/api/auth/logout/` | 토큰 블랙리스트 등록 |
| POST | `/api/auth/token/refresh/` | access 토큰 갱신 |
| GET  | `/api/auth/me/` | 현재 사용자 정보 |

**워크스페이스 UI 엔드포인트** (템플릿 기반)

| Method | Path | 설명 |
|--------|------|------|
| GET  | `/workspace/dashboard/` | 내 특허 프로젝트 목록 |
| GET/POST | `/workspace/create/` | 새 특허 프로젝트 생성 |
| GET  | `/workspace/workstation/<id>/` | 프로젝트 워크스테이션 |
| GET  | `/workspace/mypage/` | 마이페이지 |

**회원가입 → 로그인 확인 예시**

```bash
# 1) 회원가입 (username, name, gender(M/F), age, password, password2 필수)
curl -s -X POST http://localhost:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","name":"테스터","gender":"M","age":25,"password":"test1234!","password2":"test1234!"}' \
  | python3 -m json.tool

# 2) 로그인 → access 토큰 획득
curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test1234!"}' | python3 -m json.tool
```

---

### 4. fastapi `:8080` — 멀티에이전트 파이프라인 API

```bash
curl -s http://localhost:8080/health
# → {"status":"ok","service":"patent-agent"}
```

**주요 엔드포인트**

| Method | Path | 설명 |
|--------|------|------|
| GET  | `/health` | 서버 상태 확인 |
| POST | `/api/pipeline/run` | 파이프라인 새로 실행 |
| POST | `/api/pipeline/continue` | 기존 파이프라인 이어서 실행 |
| POST | `/api/agents/{name}/run` | 특정 에이전트 단독 실행 |
| GET  | `/api/runs/{run_id}` | 실행 상태·결과 조회 |

**파이프라인 실행 예시**

```bash
# 1) 파이프라인 실행 (동기 — 완료될 때까지 대기 후 결과 반환)
curl -s -X POST http://localhost:8080/api/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"user_input":"자율주행 차량의 장애물 감지 시스템"}' | python3 -m json.tool
# → {"run_id": "...", "state": {...}, "decision": {...}}

# 2) 실행 이력 조회 (run_id로 저장된 결과 조회)
curl -s http://localhost:8080/api/runs/<run_id> | python3 -m json.tool
# → {"run_id":"...","status":"done","current_agent":null,"completed_agents":[...],"errors":[],...}
```

**Swagger UI** — http://localhost:8080/docs

---

### 5. frontend `:3000` — React SPA (개발 서버)

브라우저에서 http://localhost:3000 접속

Vite 개발 서버가 요청을 자동 프록시합니다:
- `/api/*` → `fastapi:8080`
- `/auth/*` → `django:8000`

---

### 6. Critic Agent — 외부 AWS vLLM 연동

Critic Agent(Examiner)는 로컬 컨테이너 없이 AWS에서 vLLM으로 서빙되는 외부 서버에 직접 연결합니다.

**연동 확인**

```bash
# vLLM 서버 헬스체크 (AWS 인스턴스에서 확인)
curl -s http://<aws-instance-ip>:8000/v1/models \
  -H "Authorization: Bearer <RUNPOD_API_KEY>" | python3 -m json.tool
# → {"object":"list","data":[{"id":"silverstone1004/exaone-3.5-7.8B-custom",...}]}
```

**동작 방식**

- `agents/examiner.py`의 `ExaminerAgent`가 시작 시 `/v1/models`를 호출해 실제 등록된 모델 ID를 확인합니다.
- 이후 OpenAI 호환 API(`/v1/chat/completions`)로 청구항 심사를 요청합니다.
- 연결에 실패하면 기본 모델명(`silverstone1004/exaone-3.5-7.8B-custom`)으로 재시도합니다.

**필요 환경변수 (`.env`)**

```dotenv
RUNPOD_VLLM_URL=http://<aws-instance-ip>:8000/v1
RUNPOD_API_KEY=<발급받은_api_key>
```

---

## 전체 스택 상태 한눈에 확인

```bash
docker compose ps
```

모든 서비스가 `running (healthy)` 상태여야 정상입니다.

```
NAME         STATUS              PORTS
postgres     running (healthy)   0.0.0.0:5432->5432/tcp
redis        running (healthy)   6379/tcp
django       running (healthy)   0.0.0.0:8000->8000/tcp
fastapi      running (healthy)   0.0.0.0:8080->8080/tcp
frontend     running             0.0.0.0:3000->3000/tcp
```

---

## 로그 확인

```bash
docker compose logs -f fastapi     # FastAPI 실시간 로그
docker compose logs -f django      # Django 실시간 로그
docker compose logs --tail=50      # 전체 서비스 최근 50줄
```

## 종료 및 데이터 초기화

```bash
# 컨테이너 중지 (데이터 유지)
docker compose down

# 컨테이너 + 볼륨 모두 삭제 (DB 초기화)
docker compose down -v
```
