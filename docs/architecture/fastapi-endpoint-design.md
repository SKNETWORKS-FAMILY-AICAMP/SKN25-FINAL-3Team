# FastAPI Agent API — 엔드포인트 설계

Django · FastAPI · Frontend 독립 배포(ADR-005) 이후 기준으로 설계된 API 표면입니다.

---

## 현재 구현 상태

| Method | Path | 상태 | 비고 |
|--------|------|------|------|
| GET    | `/health` | ✅ 구현 | |
| POST   | `/api/pipeline/run` | ✅ 구현 | 전체 파이프라인 동기 실행 |
| POST   | `/api/pipeline/continue` | ✅ 구현 | state 전체를 body로 전달 (→ deprecated 예정) |
| GET    | `/api/runs/{run_id}` | ✅ 구현 | state 포함 전체 결과 반환 |
| POST   | `/api/runs/{run_id}/agents/{name}/run` | ✅ 구현 | DB에서 state 로드 후 단일 agent 재실행 |
| POST   | `/api/agents/{name}/run` | ⚠️ deprecated | 전체 state를 body로 전달 방식, 하위호환 유지 |

---

## 목표 엔드포인트 구조 (TODO)

### 파이프라인 생명주기

```
POST   /api/pipeline/run
  req:  { user_input: string, route?: string[] }
  res:  { run_id, state, decision }
  note: 현재 동기 실행. 향후 즉시 run_id 반환 + 백그라운드 워커로 전환 예정.

GET    /api/runs/{run_id}
  res:  { run_id, status, user_input, current_agent, completed_agents,
          errors, master_decision, state, created_at, updated_at }

POST   /api/runs/{run_id}/continue                          ← TODO
  req:  { user_input?: string, route?: string[] }
  res:  { run_id, state, decision }
  note: 현재 /api/pipeline/continue 가 state 전체를 body로 전달.
        run_id만 받아 DB에서 state 로드하는 방식으로 전환해야 함.
        전환 후 /api/pipeline/continue 는 제거.
```

### Agent 재실행

```
POST   /api/runs/{run_id}/agents/{agent_name}/run           ← 구현됨
  req:  { overrides?: Record<string, unknown> }
  res:  { run_id, agent, agent_output, state }
  note: DB에서 state 로드 → agent 실행 → DB 저장.
        overrides로 특정 state key만 교체 가능 (예: user_input 수정 후 재실행).
```

### 실행 기록 (미구현)

```
GET    /api/runs/{run_id}/steps                             ← TODO
  res:  { steps: [{ step_id, agent_name, status, started_at, completed_at, output }] }
  note: run_steps 테이블 설계 및 마이그레이션 필요.
        현재는 state.workflow.trace 배열로 대체 중.

GET    /api/runs/{run_id}/artifacts                         ← TODO
  res:  { artifacts: [{ type, url, created_at }] }
  note: Object Storage(S3) 연동 후 구현.
        현재는 state.composer 아래에 rendered_markdown으로만 존재.
```

### 파이프라인 비동기화 (미구현)

```
현재 POST /api/pipeline/run 은 LLM 파이프라인 전체가 끝날 때까지 HTTP 연결을 유지함.
향후 아래 패턴으로 전환 필요:

  POST /api/pipeline/run
    → run_id 즉시 반환 (status=queued)
    → 백그라운드 워커(Celery/ARQ/RQ)가 파이프라인 실행

  GET /api/runs/{run_id}
    → 폴링으로 진행 상황 확인
    → Redis current_agent + PostgreSQL final state

후보 워커: ARQ(asyncio 기반, Redis 사용) 또는 Celery+Redis
```

---

## 인증 설계 (TODO)

Django 분리 이후 FastAPI 엔드포인트가 외부에 노출되므로 인증이 필요합니다.

### 옵션 A: Django SECRET_KEY 공유 (단기)

FastAPI가 Django와 동일한 `SECRET_KEY`로 JWT를 직접 검증합니다.

```python
# backend/fastapi/app/auth.py (미구현)
from jose import JWTError, jwt

def verify_django_jwt(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    return payload

async def get_current_user(authorization: str = Header(...)) -> dict:
    token = authorization.removeprefix("Bearer ")
    try:
        return verify_django_jwt(token)
    except JWTError:
        raise HTTPException(status_code=401)
```

```python
# 엔드포인트에 적용
@router.post("/api/pipeline/run")
async def run_pipeline(
    request: PipelineRunRequest,
    user: dict = Depends(get_current_user),  # 추가
    db: Session = Depends(get_db),
):
    ...
```

### 옵션 B: Django `/api/auth/me/` 내부 호출 (장기)

FastAPI가 수신한 JWT를 Django에 전달해 검증하는 방식.
서비스 간 latency 추가되므로 캐시(Redis) 필요.

### 현재 임시 조치

배포 전까지 FastAPI를 내부 네트워크에서만 접근 가능하도록 보안 그룹/방화벽으로 격리.
프런트엔드는 Django를 통해서만 FastAPI에 접근하거나, API Gateway를 앞에 둡니다.

---

## 프런트엔드 호출 패턴

Django 분리 후 프런트가 호출하는 순서:

```
1. POST /api/auth/login          (Django)  → access_token 획득
2. POST /api/pipeline/run        (FastAPI) → run_id 반환
3. GET  /api/runs/{run_id}       (FastAPI) → 폴링으로 상태 확인
4. POST /api/runs/{run_id}/agents/{name}/run  (FastAPI) → 단일 agent 재실행
```

Vite 프록시(개발 환경):
```
/api/auth/* → django:8000  (인증)
/api/*      → fastapi:8080 (파이프라인)
```

프로덕션 환경에서는 각 서비스의 실제 URL을 `VITE_AUTH_BASE_URL`, `VITE_API_BASE_URL`로 설정.
