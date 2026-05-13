# 프로젝트 폴더 구조와 개발 환경

이 문서는 팀원이 처음 저장소를 열었을 때 “어디에 무엇을 넣어야 하는지”를 맞추기 위한 기준입니다.

## 목표 구조

```text
SKN25-FINAL-3Team/
  README.md                 # 프로젝트 시작 안내
  BRANCH_RULES.md           # Git/PR 규칙
  pyproject.toml            # uv 기준 Python 의존성
  requirements.txt          # 보조용 의존성 목록
  .env.example              # 환경변수 예시, 실제 값 없음

  agents/                   # LLM/AI 에이전트 코드
    consultation/           # 상담 + 선행기술 + 청구항 연동 현재 코드
      consultation_agent.py
      prior_art_agent.py
      claim_agent.py
      patent_db.py
      document_utils.py
      load_corpus.py

  backend/
    django/                 # 기존 로그인/JWT Django 백엔드
      manage.py
      config/
      accounts/
      frontend/             # Django 템플릿/static 기존 화면

  frontend/                 # 향후 React + TypeScript 프론트엔드
    README.md

  apps/
    streamlit/              # 빠른 시연/검증용 Streamlit 앱
      main.py

  data/                     # 원천/가공 데이터, 리포트, 매니페스트
    manifests/              # Drive/GCS 목록, pilot dataset 목록
    raw/                    # PDF/TXT 원천 데이터. 대용량은 Git 제외
    processed/              # 추출 JSON, payload 등. 대용량은 Git 제외
    reports/                # HTML/MD/SQLite 리포트. Git 제외

  docs/
    llm-wiki/               # 팀 문서/아키텍처/스키마/평가 기준

  scripts/                  # 데이터/운영/개발 보조 스크립트
```

## 폴더 기준

| 폴더 | 역할 | 넣으면 좋은 것 | 넣지 않을 것 |
|---|---|---|---|
| `agents/` | 상담, 선행기술, 청구항, 도면, 명세서 등 에이전트 | Python agent/module 코드 | PDF/TXT 원천 데이터, `.env` 커밋 |
| `backend/django/` | 로그인, JWT, 계정, 프로젝트 관리용 Django | Django app, settings, templates | LLM 프롬프트 실험 코드 |
| `backend/fastapi/` | 향후 FastAPI + LangGraph API | API router, graph endpoint | 화면 코드 |
| `frontend/` | 향후 React + TypeScript 화면 | React app, API client | Python agent 코드 |
| `apps/streamlit/` | 빠른 데모/검증용 앱 | Streamlit wrapper | 핵심 비즈니스 로직 |
| `data/` | 데이터/결과물 | manifest, `.gitkeep`, 작은 README | 대용량 PDF/TXT/SQLite/HTML 결과물 |
| `docs/` | 팀 문서 | 아키텍처, 스키마, 평가 기준 | 실제 API key/DB 비밀번호 |
| `scripts/` | 일회성/배치/개발 보조 | 다운로드, inventory, smoke test | 서비스 런타임 코드 |

## 환경 세팅: uv 기준

처음 한 번:

```bash
cd /home/kyung/workspace/hw/academy/final_project/SKN25-FINAL-3Team
uv venv
uv sync --dev
cp .env.example .env
```

이후 `.env`에 실제 값을 채웁니다.

```env
OPENAI_API_KEY=...
DATABASE_URL=...
CLAIM_BACKEND_URL=...
SECRET_KEY=...
```

주의:

- `.env`는 Git에 올리지 않습니다.
- 팀원에게 공유할 값 목록은 `.env.example`만 수정합니다.
- 공통 설정은 루트 `.env`에 둡니다.
- 특정 에이전트만 덮어쓸 값은 `agents/consultation/.env`처럼 에이전트 폴더에 둘 수 있습니다. 단, 이 파일도 Git에 올리지 않습니다.

## 실행 예시

### Streamlit 상담 데모

```bash
uv run streamlit run apps/streamlit/main.py
```

### 상담 에이전트 폴더에서 직접 실행/적재

```bash
uv run python agents/consultation/load_corpus.py --dir data/raw/texts/patents_txt
```

### Django 백엔드

```bash
uv run python backend/django/manage.py migrate
uv run python backend/django/manage.py runserver 8000
```

## 앞으로 추가할 위치

```text
backend/fastapi/              # FastAPI API 서버
backend/fastapi/graphs/       # LangGraph orchestration
agents/claim/                 # 청구항 에이전트가 커지면 분리
agents/drawing/               # 도면/참조부호 에이전트
agents/specification/         # 발명의 설명/명세서 에이전트
agents/review/                # 품질/근거/리스크 검토 에이전트
frontend/                     # React + TypeScript
```

## 원칙

1. `requirements.txt`는 루트에만 둡니다. 기본은 `uv sync --dev`입니다.
2. 에이전트 폴더에는 코드만 둡니다. 원천 TXT/PDF는 `data/` 아래로 보냅니다.
3. 백엔드와 프론트엔드는 분리합니다.
4. 하드코딩된 DB 비밀번호/API URL/API key는 두지 않고 `.env`로 뺍니다.
5. 1차 MVP는 `example 600 dataset` 기준으로 상담 → 선행기술 → 청구항/도면/명세서 → 검토 리포트까지 end-to-end 관통을 우선합니다.
