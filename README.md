# SKN25-FINAL-3Team

LangGraph·FastAPI 기반 **특허 명세서 자동 작성** 멀티 에이전트 프로젝트입니다. 상세 아키텍처와 규칙은 [`CLAUDE.md`](CLAUDE.md), [`docs/architecture.md`](docs/architecture.md)를 참고하세요.

## 요구 사항

- **Python** 3.11 이상 (`.python-version` 참고)
- **uv** — 의존성 설치·실행 권장 도구 ([공식 문서](https://docs.astral.sh/uv/))

---

## Quickstart

### 1. uv 설치 (macOS)

**Homebrew**

```bash
brew install uv
```

**공식 스크립트**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 터미널을 다시 열거나 안내에 따라 PATH를 반영한 뒤 확인합니다.

```bash
uv --version
```

### 2. 저장소와 패키지 설치

```bash
git clone <저장소-URL>
cd SKN25-FINAL-3Team
uv sync
```

- 프로젝트 의존성과 개발용 도구(pytest, pytest-asyncio, ruff 등)는 `pyproject.toml`의 `[tool.uv] dev-dependencies` 기준으로 함께 설치됩니다.
- **Django 백엔드**까지 필요하면:

  ```bash
  uv sync --extra backend
  ```

### 3. 환경 변수

```bash
cp .env.example .env
```

`.env`에 `OPENAI_API_KEY`, `KIPRIS_API_KEY` 등 필요한 값을 입력합니다.

### 4. 실행

**FastAPI 에이전트 서버**

```bash
uv run uvicorn api.main:app --reload --port 8001
```

**Streamlit 프로토타입 (`app.py`)**

`app.py`는 Streamlit을 사용합니다. 아직 `pyproject.toml`에 없으면 한 번 추가합니다.

```bash
uv add streamlit
uv run streamlit run app.py
```

### 5. 테스트·린트

```bash
uv run pytest -v --tb=short
uv run ruff check .
uv run ruff format .
```

---

## pip만 사용하는 경우

uv 대신 pip를 쓸 때는 [`requirements.txt`](requirements.txt)를 참고하세요. 테스트·린트(pytest, ruff)는 별도 설치가 필요합니다.

```bash
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-asyncio ruff httpx
```

---

## 문서

| 문서 | 내용 |
|------|------|
| [`CLAUDE.md`](CLAUDE.md) | 프로젝트 규칙·모듈 맵·실행 방법 요약 |
| [`docs/architecture.md`](docs/architecture.md) | 시스템 아키텍처 |
| [`docs/conventions.md`](docs/conventions.md) | 코딩 컨벤션 |
| [`docs/interfaces/`](docs/interfaces/) | 노드별 입출력 계약 |
