# SKN25-FINAL-3Team

## 💡 꽃보다특허

**AI 기반 다중 에이전트 특허 명세서 자동 작성 플랫폼**

## 📌 Project Overview

**꽃보다특허**는 발명자의 아이디어를 바탕으로 특허 청구범위 및 명세서 초안을 자동으로 작성해 주는 **Multi-Agent 시스템**입니다.

여러 AI 에이전트(청구항 작성, 심사관 검토, 도면 기획 등)가 유기적으로 협력하여 논리적이고 견고한 특허 문서를 생성합니다.

## ✨ Key Features

* **자동 청구항 생성 (Claim Agent):** 사용자 입력을 바탕으로 독립항과 종속항의 위계 및 카테고리(장치/방법 등)를 엄밀하게 설계.
* **선행 기술 조사 (Prior Art Agent):** 사용자 발명의 신규성, 진보성 검토. 유사 선행 기술 Top-5 제공.
* **심사관 교차 검증 (Examiner Agent):** 생성된 청구항의 명확성을 파인튜닝된 에이전트가 검토하고 보정 방향성을 제시.
* **도면 기획 (Drawing Agent):** 발명 구성 요소 간의 연결성을 파악하여 블록도 및 흐름도 등의 도면 명세 초안 작성.

## 🛠️ Tech Stack

| 영역 | 기술 |
|------|------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS v4 |
| **Backend** | Python 3.12, Django (JWT 인증), FastAPI (파이프라인 API) |
| **AI / Workflow** | LangChain, OpenAI GPT-4o, AWS vLLM (Examiner Agent) |
| **Database** | PostgreSQL + pgvector (운영) / SQLite (Django 개발용) |
| **Cache / Queue** | Redis |
| **Infrastructure** | Docker, Docker Compose, uv |

## 🚀 Getting Started

#### 1. Prerequisites

* [Docker](https://www.docker.com/) 및 [Docker Compose](https://docs.docker.com/compose/) 설치 (또는 Docker Desktop)
* uv 패키지 매니저 설치 (`pip install uv`)

#### 2. Installation

```bash
# Repository Clone
git clone https://github.com/sknetworks-family-aicamp/skn25-final-3team.git
cd skn25-final-3team

# 환경 변수 설정 (.env.example 파일을 복사하여 자신의 API Key 입력)
cp .env.example .env
```

#### 3. Run Tests (로컬)

```bash
uv sync --group dev
uv run pytest
```

Docker 없이 mock 기반으로 전체 테스트를 실행합니다.

#### 4. Run the Application

```bash
docker compose up --build
```

실행 완료 후 `http://localhost:3000` 으로 접속하세요.

> 컨테이너별 확인 방법, API 엔드포인트, 로그 확인, 특허 코퍼스 DB 적재 등 상세 안내는 **[docs/QUICKSTART.md](docs/QUICKSTART.md)** 를 참조하세요.

## 📂 Project Structure

```text
skn25-final-3team/
├── agents/                     # 멀티 에이전트 파이프라인
│   ├── adapters/               # AgentAdapter 기본 클래스
│   ├── summary/                # 발명 요약 에이전트
│   ├── priorart/               # 선행기술 검색 에이전트 (pgvector)
│   ├── claim/                  # 청구항 작성 에이전트
│   ├── drawing/                # 도면 생성 에이전트
│   ├── specification/          # 명세서 작성 에이전트
│   ├── composer/               # 최종 문서 패키징 (DOCX/HTML)
│   ├── master/                 # Master Router (다음 에이전트 결정)
│   ├── schemas/                # Pydantic 출력 스키마
│   ├── graph.py                # 파이프라인 실행 오케스트레이터
│   └── state.py                # 공유 상태 정의
├── backend/
│   ├── django/                 # JWT 인증 서버 (회원가입·로그인·토큰)
│   └── fastapi/                # 파이프라인 API 서버
│       └── app/routers/        # pipeline · runs · agents 라우터
├── frontend/                   # React SPA (Vite + TypeScript + Tailwind)
├── tests/                      # 단위·통합 테스트 (pytest)
├── docs/                       # 설계 문서 및 ADR
├── docker/                     # 서비스별 Dockerfile
├── pyproject.toml              # uv 기반 의존성 관리
└── docker-compose.yml          # 로컬 개발용 컨테이너 오케스트레이션
```

## ✅ 구현 완료

- **FastAPI 파이프라인 API** — 5개 엔드포인트, PostgreSQL + Redis 연동
- **Django JWT 인증** — 회원가입 · 로그인 · 토큰 갱신 · 블랙리스트
- **React 프런트엔드** — 프로젝트 생성 · 대시보드 · 워크스테이션 · 마이페이지
- **Agent 파이프라인** — summary → prior_art → claim → drawing → specification → composer
- **Pydantic 스키마 검증** — 모든 에이전트 출력 검증 + LLM repair 루프
- **Master Router** — 사용자 입력 충분성 판단 및 다음 에이전트 결정
- **단위·통합 테스트** — pytest 3 suite, GitHub CI 연동
- **Docker Compose 환경 분리** — 프로덕션 기본(gunicorn/multi-worker), 개발 override(--reload) 분리
- **테스트 스크립트** — `scripts/test_all.sh` (전체 pytest), `scripts/smoke_test.sh` (실서버 HTTP 검증)

## 🔧 진행 중

- **Agent 로직 고도화**
  - Claim Agent: LLM 청구항 문안 품질화 로직 연결
  - Drawing Agent: SVG 렌더링 모듈 연결
  - Review Agent: 미구현 (state에 예약만 됨)
- **FastAPI 엔드포인트 정리**
  - `POST /api/runs/{run_id}/continue` — run_id 기반 파이프라인 재개 (현재 state 전체 전달 방식 교체)
  - `GET /api/runs/{run_id}/steps` — step별 실행 기록
  - `GET /api/runs/{run_id}/artifacts` — artifact 목록 (S3 연동 후)
  - 파이프라인 비동기화 — 즉시 run_id 반환 + 백그라운드 워커(ARQ/Celery)

## 📋 남은 할 일

- [ ] **FastAPI JWT 인증** — Django SECRET_KEY 공유 방식으로 토큰 검증 미들웨어 추가 (ADR-005)
- [ ] **프론트엔드 단일 에이전트 재실행 API 교체** — `WorkstationPage`의 청구항 재생성 등이 deprecated `POST /api/agents/{name}/run`(state 전체 전달)을 사용 중. `POST /api/runs/{run_id}/agents/{name}/run`으로 교체 필요 (`frontend/src/api/pipeline.ts:37`, `WorkstationPage.tsx:247, 405`)
- [ ] **claim-api healthcheck** — 모델 로딩 중 FastAPI 요청 유입 시 실패 방지
- [ ] **AWS 인프라 구성** — RDS(PostgreSQL), ElastiCache(Redis), EC2/ECS 배포
- [ ] **E2E 테스트** — 전체 파이프라인 플로우 검증 (smoke test와 별개)
- [ ] **LLM Judge 평가 파이프라인** — Agent 출력 정성 평가 지표 정의

## ⚠️ 확인 필요

- **특허 코퍼스 적재** — `agents/priorart/load_corpus.py` 스크립트는 완성. KIPRIS XML 데이터 파일 및 pgvector DB 준비 여부 확인 후 실행
- **독립 배포 환경** — docker-compose 서비스 분리는 완료. 실제 별도 서버(EC2/ECS) 배포 시 Nginx 프록시(`docker/nginx.conf`) 구성 검토 필요

## 📅 발표 자료

- **중간 발표:** [Canva PPT](https://canva.link/ht639zufailry5n)
- **최종 발표:** [Canva PPT](https://canva.link/7tgiu30dzu4k638)

## 📖 참고 문서

| 문서 | 내용 |
|------|------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | 실행 방법, 컨테이너별 확인, API 예시 |
| [docs/local-dev.md](docs/local-dev.md) | Docker 없이 로컬 개발 환경 구성 |
| [docs/testing.md](docs/testing.md) | pytest 사용법, 커버리지 확인, CI 연동 |
| [docs/corpus-loading.md](docs/corpus-loading.md) | 특허 코퍼스 DB 적재 가이드 |
| [docs/adr/](docs/adr/) | 아키텍처 결정 기록 (ADR) |
| [docs/architecture/](docs/architecture/) | API 설계, 배포 구조 |
