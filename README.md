# SKN25-FINAL-3Team

## Git 협업 안내

팀 작업은 각자 브랜치에서 진행하고, `main`에 반영할 때는 **PR(Pull Request)** 로 공유해 주세요.

```text
작업 브랜치에서 개발
→ GitHub에 push
→ main으로 PR 생성
→ PM 확인 후 merge
```

PR을 올릴 때는 아래만 가볍게 확인해 주세요.

- 작업 목적이 PR 설명에 적혀 있는지
- 불필요한 대용량 파일, 임시 파일, `.env` 같은 비밀값이 포함되지 않았는지
- 실행 또는 확인 방법이 간단히 적혀 있는지
- 은석/가영/범수/서현/홍익 담당자는 본인 확인 체크리스트를 작성했는지
- PM은 마지막에 PM 확인 체크리스트를 확인했는지

자세한 브랜치/PR 규칙과 팀원별 체크리스트는 [BRANCH_RULES.md](BRANCH_RULES.md)에 정리되어 있습니다.

---

AI/소프트웨어 특허 상담 및 선행기술 분석 프로젝트입니다.

## 개발 환경 세팅

이 프로젝트는 Python 환경을 `uv`로 맞춥니다.

```bash
cd SKN25-FINAL-3Team
uv venv
uv sync --dev
cp .env.example .env
```

그다음 `.env`에 OpenAI, DB, 외부 API 값을 채워 넣습니다. 실제 `.env`는 Git에 올리지 않습니다.

자세한 폴더 구조와 실행 방법은 [프로젝트 폴더 구조와 개발 환경](docs/PROJECT_STRUCTURE.md)에 정리되어 있습니다.

## 주요 실행 예시

```bash
# Streamlit 상담 데모
uv run streamlit run apps/streamlit/main.py

# Django 백엔드
uv run python backend/django/manage.py runserver 8000

# 특허 TXT 적재
uv run python agents/consultation/load_corpus.py --dir data/raw/texts/patents_txt
```

## 먼저 읽을 문서

프로젝트 데이터 관리, 스키마, 파이프라인, 평가 기준은 LLM Wiki에서 관리합니다.

- [프로젝트 폴더 구조와 개발 환경](docs/PROJECT_STRUCTURE.md)
- [Git 브랜치 규칙](BRANCH_RULES.md)
- [LLM Wiki 시작 문서](docs/llm-wiki/README.md)
- [LLM Wiki 목차](docs/llm-wiki/index.md)
- [팀 협업 가이드](docs/llm-wiki/concepts/team-collaboration-guide.md)
- [데이터 관리 전략](docs/llm-wiki/concepts/data-management-strategy.md)
- [Pilot 600 데이터셋](docs/llm-wiki/concepts/pilot-600-v1.md)
- [특허 데이터 스키마](docs/llm-wiki/concepts/patent-data-schemas.md)
- [파이프라인과 평가](docs/llm-wiki/concepts/pipeline-and-evaluation.md)

## 현재 폴더 구조 요약

```text
agents/             AI 에이전트 코드
  consultation/     상담 상태/DB/선행기술
  claim/            청구항 생성/저장
  drawing/          도면/참조부호/SVG
  specification/    발명의 설명/명세서/DOCX
backend/django/     Django 로그인/JWT 백엔드
frontend/           향후 React + TypeScript 프론트엔드
apps/streamlit/     빠른 검증용 Streamlit 앱
notebooks/claim/    청구항 데이터셋/학습 실험 노트북
models/claim/       청구항 모델 설정/adapter 외부 위치 기록
data/               원천/가공 데이터, 리포트, 매니페스트
docs/               팀 문서와 LLM Wiki
scripts/            데이터/운영/개발 보조 스크립트
```

## 데이터 폴더

- [data 폴더 설명](data/README.md)
- 대량 PDF/TXT/SQLite/HTML 리포트는 Git에 올리지 않습니다.
- Google Drive/GCS 원천 위치는 `data/manifests/`에서 관리합니다.
