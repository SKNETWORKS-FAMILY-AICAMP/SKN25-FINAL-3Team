# PRD: pytest 단위 테스트 스위트 및 GitHub Actions CI

**작성일:** 2026-06-02  
**상태:** Ready for Implementation  
**요구사항 유형:** 개발자/품질 요구사항

---

## Problem Statement

- 특허 AI 에이전트 서비스의 핵심 로직(파이프라인 라우팅, 스키마 검증, FastAPI 엔드포인트)에 대한 자동화된 검증 수단이 없다.
- 현재 존재하던 유일한 테스트(`test_service_skeleton.py`)는 실제 LLM API 호출이 필요한 통합 테스트로, CI 환경에서 실행할 수 없다.
- 팀원이 코드를 변경할 때 회귀(regression)를 조기에 발견하기 어렵다.
- 팀원이 각자 브랜치에서 agent adapter, master router, graph 실행 흐름을 수정할 때, 변경이 파이프라인 전체에 미치는 영향을 로컬에서 빠르게 확인할 방법이 없다.
- Pull Request가 `main`에 머지되기 전에 자동으로 검증하는 CI 파이프라인이 없다.

---

## Solution

- LLM·DB·Redis 연결 없이 실행 가능한 mock 기반 pytest 단위 테스트 스위트를 구축한다.
- PR 생성 및 `main` push 시 자동으로 실행되는 GitHub Actions 워크플로우를 연결한다.
- 테스트는 소스 코드 구조를 미러링한 디렉토리(`tests/agents/`, `tests/api/`)에 배치해 팀원이 어떤 소스 파일의 테스트를 어디서 찾아야 하는지 직관적으로 알 수 있게 한다.
- `uv run pytest` 하나로 LLM·DB 없이 전체 단위 테스트를 실행할 수 있게 한다.

---

## 유저 스토리

1. 팀원 개발자로서, `uv run pytest` 하나로 전체 단위 테스트를 실행하고 싶다. LLM API 키나 DB 없이도 로컬에서 즉시 검증할 수 있기 때문이다.

2. 팀원 개발자로서, PR을 올릴 때 GitHub Actions가 자동으로 단위 테스트를 실행하길 원한다. 팀원의 변경이 파이프라인 핵심 로직을 깨뜨리는지 머지 전에 확인할 수 있기 때문이다.

3. 팀원 개발자로서, `tests/agents/`에서 agent 로직 테스트를, `tests/api/`에서 FastAPI 엔드포인트 테스트를 찾고 싶다. 소스 파일을 수정한 뒤 어디서 테스트를 추가해야 할지 명확히 알 수 있기 때문이다.

4. 팀원 개발자로서, master router(`decide_next_agent`)의 라우팅 판단 로직이 테스트되길 원한다. summary 결과 없음→summary 실행, 발명 설명 부족→사용자 입력 요청, 전체 완료→completed 반환 같은 핵심 분기를 확신하며 수정할 수 있기 때문이다.

5. 팀원 개발자로서, `normalize_to_schema_shape`와 `safe_validate_output`이 테스트되길 원한다. LLM이 반환하는 JSON의 형식 오류(None, 단일 문자열 등)가 올바르게 교정되는지 확인할 수 있기 때문이다.

6. 팀원 개발자로서, `run_service_pipeline`이 mock adapter로 테스트되길 원한다. 실제 LLM 호출 없이 파이프라인 실행 흐름(정상 완료, 검증 실패, 콜백 호출, 부분 route)을 검증할 수 있기 때문이다.

7. 팀원 개발자로서, `SummaryAdapter`가 테스트되길 원한다. 짧은 입력(30자 미만)일 때 `needs_user_input` 상태를 반환하고, 긴 입력일 때 `ok`를 반환하는 동작을 확신할 수 있기 때문이다.

8. 팀원 개발자로서, `POST /api/pipeline/run` 엔드포인트가 mock DB로 테스트되길 원한다. run_id 생성, DB 저장, state 반환, 잘못된 입력에 대한 422 응답이 올바른지 확인할 수 있기 때문이다.

9. 팀원 개발자로서, `GET /api/runs/{run_id}` 엔드포인트가 테스트되길 원한다. Redis current_agent 조회, Redis 장애 시 DB fallback, 존재하지 않는 run_id에 대한 404 응답이 올바른지 확인할 수 있기 때문이다.

10. 팀원 개발자로서, `create_initial_state()`의 반환 구조가 테스트되길 원한다. workflow 초기값, document_links 구조, drafting_options 기본값이 계약대로 생성되는지 확신할 수 있기 때문이다.

11. 팀원 개발자로서, `AgentValidationError`의 메시지 포맷이 테스트되길 원한다. 검증 실패 시 agent 이름, 재실행 힌트(`/api/agents/{name}/run`), repair 오류가 에러 메시지에 포함되는지 확인할 수 있기 때문이다.

12. 인프라 담당자로서, GitHub Actions가 `uv sync --frozen --only-group shared --only-group fastapi --only-group django --only-group dev`로 의존성을 설치하길 원한다. `uv.lock`을 기준으로 재현 가능한 CI 환경을 보장할 수 있기 때문이다.

13. 팀원 개발자로서, 테스트가 실제 DB 연결 없이 실행되길 원한다. `DATABASE_URL` 환경변수만 dummy 값으로 설정하면 로컬에서도, CI에서도 동일하게 동작하기 때문이다.

---

## Implementation Decisions

### 테스트 계층 구조 (소스 미러링)

```
tests/
  conftest.py          — 공유 fixture (state, mock DB session, mock Run record)
  agents/
    test_state.py      — agents/state.py
    test_validation.py — agents/validation.py
    test_master_router.py — agents/master/router.py
    test_graph.py      — agents/graph.py
    test_summary_adapter.py — agents/summary/adapter.py
  api/
    test_pipeline.py   — backend/fastapi/app/routers/pipeline.py
    test_runs.py       — backend/fastapi/app/routers/runs.py
```

`tests/agents/`와 `tests/api/`에 `__init__.py`를 두지 않는다. 이유: `agents/`라는 실제 패키지와 이름이 충돌해 pytest가 `agents.test_state`로 잘못 import하기 때문이다.

### 외부 의존성 처리

- **LLM**: 각 agent adapter의 `call_agent()`를 `MagicMock`으로 교체
- **PostgreSQL**: `get_db` FastAPI 의존성을 `MagicMock` session으로 override
- **Redis**: `_redis` 모듈 변수를 `patch()`로 대체
- **DATABASE_URL**: `conftest.py` 최상단에서 `os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")`로 설정 — `db.py`가 임포트 시 RuntimeError를 발생시키는 것을 방지

### pytest 설정 (`pyproject.toml`)

- `testpaths = ["tests"]`
- `asyncio_mode = "auto"` (pytest-asyncio)
- `pythonpath = ["."]` + 루트 `conftest.py`의 `sys.path.insert`로 이중 보장

### 의존성 추가 (dev group)

- `pytest-mock>=3.14` — `mocker` fixture로 간결한 mock 작성
- `pytest-asyncio>=0.24` — FastAPI async endpoint 테스트 지원

### GitHub Actions 워크플로우

- 트리거: `pull_request` (branches: main) + `push` (branches: main)
- 환경: `ubuntu-latest`, Python 3.11
- 의존성 설치: `astral-sh/setup-uv@v4` → `uv sync --frozen --only-group shared --only-group fastapi --only-group django --only-group dev`
- 테스트 실행: `uv run pytest -v --tb=short`
- `DATABASE_URL`, `REDIS_URL`은 workflow env로 dummy 값 주입

### state key 매핑 계약

agent 이름과 state 저장 키가 다른 경우(`claim` → `claims`, `composer` → `final_package`)는 각 adapter의 `state_key`가 단일 기준이다. `build_agent_state_key_map()`이 이를 dict로 변환해 `decide_next_agent()`에 전달한다.

---

## Testing Decisions

### 좋은 테스트의 기준

- **외부 동작만 검증한다**: 함수의 반환값, 상태 변경, 예외 발생 여부를 테스트한다. 내부 구현(private 메서드, 변수명)은 테스트하지 않는다.
- **단일 책임**: 테스트 하나는 하나의 동작을 검증한다. 여러 assert를 묶지 않는다.
- **가장 높은 seam 사용**: adapter.run() > call_agent() 순으로 가능한 높은 계층에서 테스트한다.
- **LLM/DB/Redis는 항상 mock**: 단위 테스트에서 네트워크 요청은 발생하지 않는다.

### 테스트 대상 모듈

| 모듈 | 핵심 검증 내용 |
|---|---|
| `agents/state.py` | `create_initial_state()`의 초기값 계약 |
| `agents/validation.py` | normalize 변환 규칙, safe_validate 성공/실패 경로 |
| `agents/master/router.py` | `decide_next_agent()` 분기 (no summary, short input, partial pipeline, completed) |
| `agents/graph.py` | `run_service_pipeline()` 흐름 (완료, 검증 실패, partial route, progress callback) |
| `agents/summary/adapter.py` | 짧은/긴 입력 구분, 스키마 검증 통과 |
| `FastAPI pipeline router` | run_id 반환, DB 저장, 422 처리 |
| `FastAPI runs router` | Redis current_agent, Redis fallback, 404 처리 |

### Prior art

`tests/conftest.py`의 `make_mock_adapter()` helper가 adapter mock 생성의 공통 패턴을 제공한다. 새 agent adapter 테스트 작성 시 이 패턴을 따른다.

FastAPI 테스트는 `starlette.testclient.TestClient`를 사용하며, `app.dependency_overrides[get_db]`로 DB 의존성을 교체하는 방식을 일관되게 적용한다.

---

## Out of Scope

- **실제 LLM 호출 검증**: 프롬프트 품질, 생성 결과의 정확성은 통합 테스트 또는 수동 검토 범위다.
- **Django auth 모듈 테스트**: Django accounts/JWT 관련 테스트는 별도 계획 필요.
- **데이터베이스 마이그레이션 검증**: alembic 마이그레이션 정합성 테스트는 별도 CI 작업으로 분리한다.
- **프론트엔드(React) 테스트**: 이 PRD는 백엔드 Python 코드에 한정한다.
- **부하 테스트 / 성능 테스트**: 단위 테스트의 범위 밖이다.
- **`review` agent 테스트**: 해당 agent가 아직 미구현(`TODO` 상태)이므로 구현 완료 후 별도 추가한다.
- **claim, drawing, specification, priorart adapter 테스트**: 이번 스코프에서는 SummaryAdapter만 포함. 나머지는 각 담당자가 동일한 패턴으로 추가한다.

---

## Further Notes

- `uv run pytest -v` 명령이 CI와 로컬 모두에서 사용하는 표준 실행 명령이다. 팀원 전원이 PR 전에 이 명령으로 로컬 검증을 완료해야 한다.
- 새 agent adapter를 추가할 때는 `tests/agents/test_{agent_name}_adapter.py`를 함께 만든다. `test_summary_adapter.py`가 템플릿 역할을 한다.
- `DATABASE_URL`이 없는 환경에서 `db.py`가 `RuntimeError`를 발생시키는 설계는 의도적이다. CI에서는 workflow env, 로컬에서는 `conftest.py`의 `setdefault`가 이를 처리한다.
- `tests/agents/__init__.py` 추가 여부는 자유다. `--import-mode=importlib` 설정 덕분에 pytest가 절대 경로로 테스트 파일을 임포트하므로 `agents` 패키지와 이름 충돌이 발생하지 않는다.
