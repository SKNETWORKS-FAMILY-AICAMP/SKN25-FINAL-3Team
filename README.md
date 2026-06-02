## 📅 프로젝트 진행 상황

- **중간 발표 자료:** [Canva PPT 링크](https://canva.link/ht639zufailry5n)

# SKN25-FINAL-3Team

## AI 기반 특허 작성 보조 Agent Service

개인 발명가의 아이디어를 입력받아 변리사가 검토 가능한 특허 초안, 선행기술 검토, 청구항, 도면, 명세서 초안을 생성하는 AI Agent 기반 특허 작성 보조 서비스입니다.

이제 구조의 기준은 중간발표용 단방향 데모가 아니라 **서비스 API + Master Router + Graph + Adapter + Schema + State**입니다. 각 agent는 독립 구현하되, 서비스에는 Pydantic schema와 adapter 계약을 통해 연결합니다.

## 주요 범위

- 발명 입력 요약 및 부족 정보 질문 생성
- 선행기술조사 및 유사 특허 검색
- 청구항 초안 생성
- 도면 초안 생성
- 명세서 초안 생성
- 최종 패키지/검토 결과 조회

## 주요 폴더 구조

```text
agents/                  Agent, schema, shared state, graph, master/router
agents/schemas/          Agent별 Pydantic output 계약
agents/adapters/         service graph와 실제 agent 구현 사이의 변환 계층
backend/fastapi/app/     FastAPI 서비스 진입점과 pipeline API
frontend/                React/TypeScript 프론트엔드 자리
```

## 서비스 실행 흐름

```text
Frontend / API Client
  ↓
FastAPI
  ↓
Master Router
  ↓
Graph
  ↓
Agent Adapter
  ↓
Agent Output Schema Validation
  ↓
Run State / Artifacts
```

## 기본 API 초안

```text
GET  /health
POST /api/pipeline/run
POST /api/pipeline/continue
```

`/run`은 새 실행 상태를 만들고, `/continue`는 기존 state와 추가 사용자 입력을 받아 다음 단계 판단을 이어갑니다.

## 데이터 관리 안내

대량 특허 PDF/XML 원천 데이터는 AWS S3 등 외부 저장소에서 관리하며, GitHub에는 소스 코드, 문서, 데이터 매니페스트, 샘플 데이터 중심으로 정리합니다.

API Key, AWS 인증 정보, `.env` 파일 등 민감 정보는 GitHub에 포함하지 않습니다.
