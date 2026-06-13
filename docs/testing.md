# 테스트 가이드

pytest 하나로 **Django**, **FastAPI**, **Agents** 세 영역을 모두 실행합니다.

---

## 테스트 구조

```
tests/
├── conftest.py          # 공통 fixture (AgentState, mock DB/Redis)
├── agents/              # LangGraph 에이전트 유닛테스트
│   ├── test_state.py
│   ├── test_graph.py
│   ├── test_master_router.py
│   ├── test_summary_adapter.py
│   └── test_validation.py
├── api/                 # FastAPI 엔드포인트 테스트 (TestClient)
│   ├── conftest.py
│   ├── test_runs.py
│   └── test_pipeline.py
└── django/              # Django 모델 · REST API 테스트
    ├── test_accounts.py
    └── test_workspace.py
```

---

## 사전 준비

```bash
uv sync --group dev
```

`dev` 그룹은 pytest, pytest-django, pytest-asyncio, pytest-mock을 포함합니다.

---

## 기본 실행

```bash
# 전체 테스트
uv run pytest

# 특정 영역만
uv run pytest tests/django/
uv run pytest tests/api/
uv run pytest tests/agents/

# 특정 파일
uv run pytest tests/django/test_accounts.py

# 특정 테스트 함수
uv run pytest tests/django/test_accounts.py::test_login_success
```

---

## 자주 쓰는 옵션

| 옵션 | 설명 |
|---|---|
| `-v` | 테스트 이름 상세 출력 |
| `-x` | 첫 번째 실패 시 즉시 중단 |
| `-k "keyword"` | 이름에 키워드가 포함된 테스트만 실행 |
| `--tb=short` | 에러 트레이스백 간략 출력 |
| `--no-header` | pytest 헤더 생략 (CI 로그 정리용) |
| `-q` | 최소 출력 |

```bash
# 예: 로그인 관련 테스트만 빠르게 실행
uv run pytest -k "login" -v

# 예: 실패 즉시 멈추고 짧은 트레이스백
uv run pytest -x --tb=short
```

---

## 커버리지 확인

### 설치

```bash
uv add --group dev pytest-cov
uv sync --group dev
```

### 실행

```bash
# 터미널 리포트
uv run pytest --cov=. --cov-report=term-missing
```

### 커버리지 측정 범위 지정

불필요한 경로(마이그레이션, .venv 등)를 제외하려면 `pyproject.toml`에 추가합니다.

```toml
[tool.coverage.run]
omit = [
    ".venv/*",
    "*/migrations/*",
    "*/manage.py",
    "*/wsgi.py",
    "*/asgi.py",
]
source = [
    "agents",
    "backend/fastapi/app",
    "backend/django",
]

[tool.coverage.report]
show_missing = true
skip_covered = false
```

설정 후 실행:

```bash
uv run pytest --cov
```

### 최소 커버리지 강제 (CI용)

```bash
# 80% 미만이면 exit code 1 반환
uv run pytest --cov --cov-fail-under=80
```

---

## Django 테스트 관련 참고

- `@pytest.mark.django_db` 데코레이터가 있어야 DB 접근이 허용됩니다.
- 각 테스트는 트랜잭션 롤백으로 격리되므로 테스트 순서에 영향을 받지 않습니다.
- DB는 SQLite in-memory(`:memory:`)를 사용해 실제 PostgreSQL 없이도 실행됩니다.
- 설정 파일: [backend/django/config/test_settings.py](../backend/django/config/test_settings.py)

---

## FastAPI 테스트 관련 참고

- `TestClient`로 HTTP 요청을 흉내내며 실제 서버 없이 실행됩니다.
- DB는 `MagicMock`으로 대체되어 PostgreSQL 없이도 실행됩니다.
- `tests/api/conftest.py`에서 `get_db` 의존성을 mock으로 교체합니다.

---

## CI에서 실행하는 방법

```yaml
# GitHub Actions 예시
- name: Run tests
  run: |
    uv sync --group dev
    uv run pytest --tb=short --no-header -q
```
