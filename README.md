# 🌸 꽃보다특허

> 발명 아이디어를 청구항, 선행기술조사, 특허 도면, 명세서 초안으로 연결하는 AI 기반 Multi-Agent 특허 작성 플랫폼

## 📌 프로젝트 소개

**꽃보다특허**는 발명자가 입력하거나 논문에서 추출한 기술 정보를 바탕으로 특허 문서 작성 과정을 지원합니다.

- React 워크스페이스와 Django API가 사용자·프로젝트·문서를 관리하고,
- FastAPI AI Worker가 LangGraph 기반 에이전트 파이프라인을 실행합니다.
- Claim(청구항), Examiner(심사관), Prior Art(선행기술조사), Drawing(도면), Specification(발명의 설명)등의 **멀티 에이전트**가 구조화된 상태를 공유하며 청구항 작성부터 검토·보정까지 연결합니다.

## 🎬 시연 영상

<!-- GitHub README 편집 화면에 `SKN 3팀 시연 영상.mov`를 드래그해 생성되는 user-attachments URL로 아래 링크를 교체하세요. -->


https://github.com/user-attachments/assets/f180f1c0-1f70-4c0d-b356-a14f2b1cdf15







## 👥 팀원 소개

| &nbsp;&nbsp;이름&nbsp;&nbsp;   | GitHub                               | 역할                           | 담당 영역                                    |
| ---------------- | ------------------------------------ | ------------------------------ | -------------------------------------------- |
| 권가영 | [@Gayoung03](https://github.com/Gayoung03) | Frontend / AI Agent  | React 화면, 명세서 Agent 연동, 청구항 단독 심사 기능 구현, 사용자 편의 기능 기획 및 개선, pytest 기반 테스트 코드 작성               |
| 김서현 | [@bizseohyunkim](https://github.com/bizseohyunkim)  | Frontend / AI Agent                       | 도면(Drawing) 에이전트 개발, 웹 UI 개발     |
| 김홍익 | [GitHub](https://github.com/userid)  | Django Backend                 | 계정, 프로젝트, 문서 저장 API                |
| 박범수 | [@bumwater](https://github.com/bumwater)  | DB / AI Agent             | 선행기술 데이터 적재, 선행기술 조사 기능 구현, RAGAS 평가 지표 구현       |
| 조은석 | [@silverstone-1004](https://github.com/silverstone-1004)  | AI Agent / Infra      | Langchain, Langgraph, Langsmith, fintetuning, 배포·운영      |
| 팀원 6 | [GitHub](https://github.com/userid)  | Data / Evaluation / Infra      | 선행기술 데이터, 평가, 배포·운영 환경        |

## ✨ 주요 기능

<table>
<tr>
<td width="50%" valign="top" style="white-space: nowrap;">

### 💡 1. 발명 입력·구체화

- 발명 프로젝트 생성 및 관리
- PDF·DOCX·HWP 논문 분석
- 발명 핵심 요소 자동 구조화

</td>
<td width="50%" valign="top" style="white-space: nowrap;">

### 📝 2. 특허 문서 생성

- 독립항·종속항 자동 작성
- Graphviz 기반 특허 도면 생성
- 청구항·도면 기반 명세서 작성

</td>
</tr>
<tr>
<td width="50%" valign="top" style="white-space: nowrap;">

### ⚖️ 3. 심사·검증·보정

- AI 심사관 청구항 명확성 심사
- 거절 사유 기반 자동 보정
- 사용자 작성 청구항 실시간 심사

</td>
<td width="50%" valign="top" style="white-space: nowrap;">

### 🔍 4. 조사·저장·보고

- pgvector·KIPRIS 유사특허 검색
- 신규성·진보성 위험도 분석
- 청구항·도면·명세서 통합 보고서

</td>
</tr>
</table>


## 🧭 시스템 구조

<img width="2109" height="947" alt="시스템" src="https://github.com/user-attachments/assets/c54f835a-3faf-469b-b16c-2a9f6e6f8fd7" />


## 🛠️ 기술 스택

### Frontend

<p>
  <img src="https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react&logoColor=white" alt="React 18.3.1">
  <img src="https://img.shields.io/badge/TypeScript-5.5.3-3178C6?logo=typescript&logoColor=white" alt="TypeScript 5.5.3">
  <img src="https://img.shields.io/badge/Vite-5.4.1-646CFF?logo=vite&logoColor=white" alt="Vite 5.4.1">
  <img src="https://img.shields.io/badge/React_Router-6.26.0-CA4245?logo=reactrouter&logoColor=white" alt="React Router 6.26.0">
  <img src="https://img.shields.io/badge/Tailwind_CSS-4.3.0-06B6D4?logo=tailwindcss&logoColor=white" alt="Tailwind CSS 4.3.0">
  <img src="https://img.shields.io/badge/PostCSS-8.5.15-DD3A0A?logo=postcss&logoColor=white" alt="PostCSS 8.5.15">
  <img src="https://img.shields.io/badge/Autoprefixer-10.5.0-DD3735?logo=autoprefixer&logoColor=white" alt="Autoprefixer 10.5.0">
</p>

### Backend

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/Django-6.0.6-092E20?logo=django&logoColor=white" alt="Django 6.0.6">
  <img src="https://img.shields.io/badge/Django_REST_Framework-3.17.1-A30000?logo=django&logoColor=white" alt="Django REST Framework 3.17.1">
  <img src="https://img.shields.io/badge/FastAPI-0.136.3-009688?logo=fastapi&logoColor=white" alt="FastAPI 0.136.3">
  <img src="https://img.shields.io/badge/Uvicorn-0.49.0-499848?logo=gunicorn&logoColor=white" alt="Uvicorn 0.49.0">
  <img src="https://img.shields.io/badge/SimpleJWT-5.5.1-000000?logo=jsonwebtokens&logoColor=white" alt="SimpleJWT 5.5.1">
  <img src="https://img.shields.io/badge/drf--spectacular-0.29.0-7B1FA2?logo=swagger&logoColor=white" alt="drf-spectacular 0.29.0">
</p>

### AI / Agent

<p>
  <img src="https://img.shields.io/badge/OpenAI-2.41.0-412991?logo=openai&logoColor=white" alt="OpenAI 2.41.0">
  <img src="https://img.shields.io/badge/LangChain-1.3.4-1C3C3C?logo=langchain&logoColor=white" alt="LangChain 1.3.4">
  <img src="https://img.shields.io/badge/LangGraph-1.2.4-1C3C3C?logo=langchain&logoColor=white" alt="LangGraph 1.2.4">
  <img src="https://img.shields.io/badge/LangChain_OpenAI-1.2.2-412991?logo=openai&logoColor=white" alt="LangChain OpenAI 1.2.2">
  <img src="https://img.shields.io/badge/LangSmith-0.8.11-2E7D32?logo=langchain&logoColor=white" alt="LangSmith 0.8.11">
  <img src="https://img.shields.io/badge/Pydantic-2.13.4-E92063?logo=pydantic&logoColor=white" alt="Pydantic 2.13.4">
  <img src="https://img.shields.io/badge/RunPod-vLLM-673AB7?logo=runpod&logoColor=white" alt="RunPod vLLM">
</p>

### Data

<p>
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/pgvector-0.4.2-336791?logo=postgresql&logoColor=white" alt="pgvector 0.4.2">
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0.50-D71F00?logo=sqlalchemy&logoColor=white" alt="SQLAlchemy 2.0.50">
  <img src="https://img.shields.io/badge/psycopg2-2.9.12-336791?logo=postgresql&logoColor=white" alt="psycopg2 2.9.12">
  <img src="https://img.shields.io/badge/SQLite-Local_%2F_Test-003B57?logo=sqlite&logoColor=white" alt="SQLite Local and Test">
  <img src="https://img.shields.io/badge/AWS_S3-Storage-569A31?logo=amazons3&logoColor=white" alt="AWS S3">
  <img src="https://img.shields.io/badge/boto3-1.43.32-FF9900?logo=amazonaws&logoColor=white" alt="boto3 1.43.32">
</p>

### Infrastructure

<p>
  <img src="https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/Docker_Compose-Orchestration-2496ED?logo=docker&logoColor=white" alt="Docker Compose">
  <img src="https://img.shields.io/badge/uv-0.9.17-DE5FE9?logo=astral&logoColor=white" alt="uv 0.9.17">
  <img src="https://img.shields.io/badge/pytest-9.1.1-0A9EDC?logo=pytest&logoColor=white" alt="pytest 9.1.1">
  <img src="https://img.shields.io/badge/Graphviz-0.21-2596BE?logo=graphviz&logoColor=white" alt="Graphviz 0.21">
  <img src="https://img.shields.io/badge/PyGraphviz-1.14-2596BE?logo=graphviz&logoColor=white" alt="PyGraphviz 1.14">
  <img src="https://img.shields.io/badge/PyMuPDF-1.27.2.3-00897B?logo=adobeacrobatreader&logoColor=white" alt="PyMuPDF 1.27.2.3">
  <img src="https://img.shields.io/badge/python--docx-1.2.0-2B579A?logo=microsoftword&logoColor=white" alt="python-docx 1.2.0">
</p>

### External API

<p>
  <img src="https://img.shields.io/badge/OpenAI_API-LLM-412991?logo=openai&logoColor=white" alt="OpenAI API">
  <img src="https://img.shields.io/badge/RunPod_API-vLLM-673AB7?logo=runpod&logoColor=white" alt="RunPod API">
  <img src="https://img.shields.io/badge/KIPRIS_API-Patent_Search-005BAC?logo=searchengin&logoColor=white" alt="KIPRIS API">
  <img src="https://img.shields.io/badge/LangSmith-Tracing-2E7D32?logo=langchain&logoColor=white" alt="LangSmith">
  <img src="https://img.shields.io/badge/AWS-RDS_%2F_S3-FF9900?logo=amazonaws&logoColor=white" alt="AWS RDS and S3">
</p>

## 📂 프로젝트 구조

```text
SKN25-FINAL-3Team/
├── agents/
│   ├── core/                  # Pydantic state와 LangGraph workflow
│   ├── consultation/          # 상담 흐름 보조 로직
│   ├── prior_art_agent/       # pgvector/KIPRIS 선행기술조사
│   ├── schemas/               # 에이전트 공통 schema
│   ├── specification/         # 명세서 생성·검증·저장 헬퍼
│   ├── summary_agent.py       # 발명 정보 구조화
│   ├── claim_agent.py         # 청구항 생성
│   ├── examiner.py            # 청구항 심사
│   ├── claim_rewrite_agent.py # 거절 사유 기반 보정
│   ├── drawing_agent.py       # 도면 생성
│   └── paper_analyzer.py      # 논문 분석
├── backend/
│   ├── django/
│   │   ├── accounts/         # JWT 계정 API
│   │   ├── workspace/        # 프로젝트·상담·문서 저장 API
│   │   ├── core/             # Django 기본 페이지
│   │   ├── static/           # Django 정적 파일
│   │   ├── templates/        # Django 공통 템플릿
│   │   └── config/           # Django settings, URL, ASGI
│   └── fastapi/
│       ├── routers/           # 청구항·심사·도면·명세서·특허검색 worker
│       ├── judge/             # LangSmith LLM-as-a-Judge
│       └── main.py            # FastAPI entrypoint
├── frontend/
│   ├── public/                # favicon 등 정적 리소스
│   └── src/
│       ├── api/               # Django/FastAPI API client
│       ├── components/        # 공통 UI와 modal
│       ├── contexts/          # 인증 context
│       └── pages/             # Home, Dashboard, Workstation, Report 등
├── tests/
│   ├── agents/                # 에이전트·state·graph 단위 테스트
│   ├── api/                   # FastAPI worker·stream·인증 경계 테스트
│   ├── django/                # 계정·workspace 모델과 view 테스트
│   └── README.md              # 테스트 실행법과 파일별 목적
├── evals/
│   └── specification/         # 명세서 생성 품질 평가 case와 judge
├── fine-tuning/               # Examiner 모델 파인튜닝 자료
├── data/                      # 선행기술 데이터
├── drawings/                  # 로컬 도면 생성 산출물
├── scripts/                   # 데이터·운영 보조 스크립트
├── .env.example               # 환경변수 예시
├── pyproject.toml             # Python 의존성
├── uv.lock                    # Python lock file
├── Dockerfile                 # Django/FastAPI 공통 이미지
├── docker-compose.yml         # Django와 FastAPI 서비스 구성
└── nginx.conf                 # 배포 reverse proxy 설정
```

## 🚀 실행 방법

### 1. 사전 준비

- Docker 및 Docker Compose
- [uv](https://docs.astral.sh/uv/)
- React 프런트엔드를 실행하려면 Node.js와 npm

### 2. 저장소와 환경변수 준비

```bash
git clone https://github.com/sknetworks-family-aicamp/skn25-final-3team.git
cd skn25-final-3team
cp .env.example .env
```

`.env`에는 사용하는 기능에 맞게 다음 값을 설정합니다.

| 구분 | 주요 환경변수 |
|---|---|
| LLM | `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_CHAT_MODEL` |
| Examiner | `RUNPOD_VLLM_URL`, `RUNPOD_API_KEY` |
| 선행기술 DB | `RDS_DATABASE_URL`, `PRIOR_ART_ANALYZE_MAX_WORKERS` |
| Django DB | `DJANGO_DB_ENGINE`, `DJANGO_DB_NAME`, `DJANGO_DB_USER`, `DJANGO_DB_PASSWORD`, `DJANGO_DB_HOST`, `DJANGO_DB_PORT` |
| 특허 검색 | `KIPRIS_API_KEY` |
| AWS | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `S3_BUCKET` |
| 추적 | `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY` |

### 3. Django와 FastAPI 실행

```bash
docker compose up --build
```

| 서비스 | 주소 |
|---|---|
| Django 메인 서버 | `http://localhost:8000` |
| Django API 문서 | `http://localhost:8000/api/docs/` |
| FastAPI AI Worker | `http://localhost:8001` |
| FastAPI API 문서 | `http://localhost:8001/docs` |

### 4. React 프런트엔드 실행

현재 `docker-compose.yml`에는 프런트엔드 서비스가 없으므로 별도 터미널에서 실행합니다.

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:3000`으로 접속합니다. Vite proxy가 `/auth`와 `/api/v1/workspace` 요청은 Django로, 그 외 `/api` 요청은 FastAPI로 전달합니다.


## 🔌 주요 API 흐름

| 구분 | Django/FastAPI 경로 | 역할 |
|---|---|---|
| 계정 | `/accounts/` | signup, login, logout, me, token refresh |
| Workspace | `/workspace/` | 프로젝트·상담·청구항·도면·명세서 관리 |
| 청구항 생성 | `/api/v1/generate-claims` | LangGraph 기반 청구항 생성·심사·선행기술 스트림 |
| 사용자 청구항 심사 | `/api/v1/review-claims` | 청구항 분석·심사·보정 NDJSON 스트림 |
| 도면 생성 | `/api/v1/generate-drawings` | Graphviz 도면 생성 및 S3 업로드 |
| 명세서 생성 | `/api/v1/generate-specification` | 발명의 설명 생성과 검증 |
| 특허 검색 | `/api/v1/patent-search` | KIPRIS 특허 검색 |

## 📅 프로젝트 진행 상황

- pytest 테스트 체계 재구성: **108/108 통과**
- 사용자 작성 청구항 심사·자동 보정 흐름 반영
- **시연 영상:** README 상단의 GitHub 업로드 URL로 연결
- **최종 발표 자료:** [Canva PPT 링크](https://canva.link/7tgiu30dzu4k638)
