---
title: Developer Workflow Scenario
created: 2026-05-12
updated: 2026-05-12
type: guide
tags: [collaboration, data]
sources: []
confidence: high
---

# Developer Workflow Scenario

## 한 줄 요약

코드를 고치기 전과 후에 LLM Wiki를 확인하면, 팀원이 서로 다른 방향으로 개발하는 일을 줄일 수 있습니다.

## 이 문서를 언제 보나

팀원이 아래 일을 할 때 봅니다.

- 새 기능 개발
- 버그 수정
- 데이터 처리 스크립트 작성
- JSON 구조 변경
- 폴더 구조 변경
- AI에게 코드 수정을 맡기기 전
- Git push / PR 올리기 전

## 시나리오: 팀원이 상담 에이전트 코드를 고치는 경우

### 1. 개발 시작 전

먼저 Git 최신화합니다.

```bash
git checkout main
git pull origin main
git checkout 내브랜치명
git merge main
```

그다음 LLM Wiki에서 관련 문서를 봅니다.

```text
docs/llm-wiki/index.md
→ docs/llm-wiki/concepts/data-management-strategy.md
→ docs/llm-wiki/concepts/patent-data-schemas.md
→ docs/llm-wiki/concepts/agent-architecture-notes.md
```

확인할 것:

- 지금 개발 데이터가 PDF인지, 가상 상담내역인지
- 어떤 JSON을 입력으로 받고 어떤 JSON을 출력해야 하는지
- 아직 확정되지 않은 부분이 뭔지
- 대량 PDF/TXT를 Git에 올리면 안 된다는 점

### 2. AI에게 코드 수정을 맡길 때

AI에게 그냥 “코드 고쳐줘”라고 하지 말고, 관련 LLM Wiki 문서를 같이 알려줍니다.

예시 프롬프트:

```text
이 프로젝트는 docs/llm-wiki/index.md를 기준으로 개발한다.
특히 아래 문서를 먼저 읽고 작업해라.
- docs/llm-wiki/concepts/data-management-strategy.md
- docs/llm-wiki/concepts/patent-data-schemas.md
- docs/llm-wiki/concepts/agent-architecture-notes.md

이번 작업은 상담 에이전트가 simulated_consultation을 입력받아 invention_payload를 만들도록 수정하는 것이다.
확정되지 않은 JSON 필드는 임의로 많이 만들지 말고 TODO로 남겨라.
대량 PDF/TXT, .env, SQLite는 Git에 포함하지 마라.
작업 후 변경된 설계가 있으면 docs/llm-wiki에 반영할 문서도 알려줘라.
```

### 3. 개발 중

코드를 고치다가 Wiki 내용과 다르면 둘 중 하나를 해야 합니다.

| 상황 | 해야 할 일 |
|---|---|
| 코드가 Wiki와 다르게 구현됨 | 코드가 잘못된 건지 Wiki가 오래된 건지 확인 |
| JSON 필드를 새로 추가함 | `patent-data-schemas.md`에 후보 필드로 기록 |
| 데이터 폴더를 바꿈 | `data-management-strategy.md` 또는 `data/README.md` 수정 |
| LangGraph node를 추가함 | `agent-architecture-notes.md` 수정 |
| 새 처리 순서가 생김 | `pipeline-and-evaluation.md` 수정 |
| 아직 확정이 아님 | `TODO`, `초안`, `예정`이라고 적기 |

### 4. 개발 끝난 후

코드만 push하지 말고 문서도 같이 확인합니다.

체크리스트:

- [ ] 내가 바꾼 코드가 LLM Wiki의 방향과 충돌하지 않는가?
- [ ] JSON 필드나 데이터 흐름을 바꿨는가?
- [ ] 바꿨다면 관련 Wiki 문서를 수정했는가?
- [ ] 새 문서를 만들었다면 `index.md`에 추가했는가?
- [ ] 중요한 변경이면 `log.md`에 남겼는가?
- [ ] PDF/TXT/DB/.env가 Git에 들어가지 않았는가?

확인 명령:

```bash
git status --short
git diff --stat
```

PDF, `.env`, SQLite가 보이면 보통 잘못된 상태입니다.

### 5. Git push / PR 전

PR 설명에 코드 변경과 문서 변경을 같이 적습니다.

예시:

```text
## 코드 변경
- simulated_consultation 입력 처리 추가
- invention_payload 생성 로직 수정

## 문서 변경
- patent-data-schemas.md에 입력/출력 관계 업데이트
- agent-architecture-notes.md에 새 node 후보 추가

## 확인
- smoke 데이터 10건 기준 실행 확인
- 대량 PDF/TXT는 Git에 포함하지 않음
```

## 가장 중요한 원칙

코드와 Wiki가 따로 놀면 안 됩니다.

- 개발 전: Wiki를 보고 방향 확인
- 개발 중: Wiki와 다른 점이 생기면 표시
- 개발 후: 코드 변경에 맞춰 Wiki 수정

## 관련 문서

- [[llm-wiki-beginner-guide]]
- [[team-collaboration-guide]]
- [[data-management-strategy]]
- [[patent-data-schemas]]
- [[agent-architecture-notes]]
- [[pipeline-and-evaluation]]
