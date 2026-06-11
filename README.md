# SKN25-FINAL-3Team

## 💡 꽃보다특허

**AI 기반 다중 에이전트 특허 명세서 자동 작성 플랫폼**



## 📌 Project Overview

**꽃보다특허**는 발명자의 아이디어를 바탕으로 특허 청구범위 및 명세서 초안을 자동으로 작성해 주는 **Multi-Agent 시스템**입니다. 

**LangGraph 기반의 여러 AI 에이전트**(청구항 작성, 심사관 검토, 도면 기획 등)가 유기적으로 협력하여 논리적이고 견고한 특허 문서를 생성합니다.

## ✨ Key Features

* **자동 청구항 생성 (Claim Agent):** 사용자 입력을 바탕으로 바탕으로 독립항과 종속항의 위계 및 카테고리(장치/방법 등)를 엄밀하게 설계.
* **선행 기술 조사 (Prior Art Agent):** 사용자 발명의 신규성, 진보성 검토. 유사 선행 기술 Top-5 제공.
* **심사관 교차 검증 (Examiner Agent):** 생성된 청구항의 명확성을 파인튜닝된 에이전트가 검토하고 보정 방향성을 제시.
* **도면 기획 (Drawing Agent):** 발명 구성 요소 간의 연결성을 파악하여 블록도 및 흐름도 등의 도면 명세 초안 작성.

## 🛠️ Tech Stack

* **Backend Core:** Python 3.12, Django
* **AI & Workflow:** LangChain, LangGraph, OpenAI
* **Infrastructure & Env:** Docker, Docker Compose, uv
* **Database:** SQLite (개발용) / PostgreSQL (운영용) / pgvector (VectorDB)

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

#### 3. Run the Application

Docker를 이용해 시스템을 빌드하고 실행합니다.

```bash
docker compose up --build
```

실행 완료 후, 브라우저에서 `http://localhost:8000`으로 접속하여 작업스페이스를 확인하세요.

## 📂 Project Structure

```text
skn25-final-3team/
├── agents/             # LangGraph 기반 다중 AI 에이전트 (청구항, 심사관, 명세서 등)
│   ├── core/           # State, Graph 정의 및 공통 모듈
│   ├── prior_art_agent/# 선행기술조사 에이전트
│   └── specification/  # 명세서 작성 에이전트
├── backend/            # Django/FastAPI 백엔드 서버 및 웹 워크스페이스
│   ├── accounts/       # 사용자 계정 관리
│   ├── workspace/      # 프로젝트 및 에이전트 상호작용 UI
│   └── test_run.py     # 로컬 에이전트 파이프라인 테스트 스크립트
├── pyproject.toml      # uv 기반 패키지 및 의존성 관리
├── Dockerfile          # 배포 및 실행 환경 정의
└── docker-compose.yml  # 컨테이너 오케스트레이션
```

## 🔃 Future Work

- FastAPI 추가
- DB Migration (Sqlite -> PostgreSQL)
- Agent logic 고도화
- Test 디렉토리 추가

## 📅 프로젝트 진행 상황

- **최종 발표 자료:** [Canva PPT 링크](https://canva.link/ht639zufailry5n)
