# Wiki Schema

## Domain

이 LLM Wiki는 **AI/소프트웨어 특허 상담 프로젝트의 팀 지식베이스**입니다.

여기에 적는 내용은 최종 확정안이 아니라, 개발하면서 바뀌는 결정을 팀이 같이 보기 위한 기록입니다.

다루는 범위:

- 프로젝트 용어와 데이터 관리 원칙
- Google Drive/manifest/로컬 데이터 폴더 규칙
- 상담 에이전트와 후속 에이전트의 설계 메모
- 아직 확정되지 않은 스키마/파이프라인의 현재 가정과 TODO
- 팀 협업 규칙과 작업 기록

## 이 문서의 역할

`SCHEMA.md`는 코드 스키마가 아니라 **LLM Wiki를 어떻게 쓸지 정한 작성 규칙 문서**입니다.

팀원이 이 파일을 매번 외울 필요는 없습니다. 문서를 새로 만들거나 구조를 바꿀 때만 참고하면 됩니다.

## YAML frontmatter란?

Markdown 파일 맨 위에 붙이는 짧은 메타데이터입니다.

예:

```yaml
---
title: Data Management Strategy
created: 2026-05-12
updated: 2026-05-12
type: concept
tags: [data, patent]
sources: []
confidence: medium
---
```

쉽게 말하면 문서의 `제목/생성일/태그/문서종류`를 적어두는 표지입니다. Obsidian, GitHub, LLM이 문서를 찾고 분류하기 쉽게 하려고 붙입니다.

## Conventions

- 파일명은 영어 소문자와 하이픈만 사용합니다. 예: `patent-data-schemas.md`
- 핵심 문서는 가능한 한 YAML frontmatter로 시작합니다.
- 핵심 문서는 서로 Obsidian식 wiki link로 연결합니다. 예: `[[data-management-strategy]]`
- 새 문서를 만들면 `index.md`에 한 줄 요약을 추가합니다.
- 중요한 변경을 하면 `log.md`에 기록합니다.
- `raw/` 아래 문서는 원천 자료 기록입니다. 원천 자체를 바꾸지 말고, 해석은 `concepts/`에 적습니다.
- 팀원이 처음 봐도 이해하도록 문장은 짧게, 표와 체크리스트를 우선합니다.
- 아직 확정되지 않은 내용은 `예정`, `가정`, `초안`, `TODO`를 명확히 표시합니다.

## Frontmatter

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: concept | source | guide | schema | decision | query
tags: [data, patent, consultation]
sources: [raw/sources/source-file.md]
confidence: high | medium | low
---
```

## Tag Taxonomy

아래 태그만 사용합니다. 새 태그가 필요하면 먼저 이 문서에 추가합니다.

- `data`: 데이터셋, manifest, 폴더 구조
- `patent`: 특허 PDF, 명세서, 청구항, 도면
- `consultation`: 상담내역, 후속 질문, 상담 상태
- `schema`: JSON 스키마, payload 구조
- `pipeline`: 처리 흐름, 스크립트, 자동화
- `evaluation`: 품질 평가, 리포트
- `collaboration`: Git/GitHub, 팀 작업 규칙
- `source`: 원천 자료 기록
- `decision`: 의사결정 기록
- `architecture`: LangGraph/LangChain, 에이전트 노드 설계

## Page Types

### source

원천 자료를 기록합니다. 예: Google Drive 폴더, 원본 PDF 묶음, 외부 문서.

필수 항목:

- 출처 URL
- 접근 방식
- 수집/분석 일자
- 파일 수 요약
- 관련 manifest 위치

### concept

프로젝트에서 반복해서 쓰는 개념을 설명합니다.

필수 항목:

- 한 줄 정의
- 왜 필요한지
- 현재 결정사항
- 다음 작업
- 관련 문서 링크

### guide

팀원이 따라 할 수 있는 절차입니다.

필수 항목:

- 목적
- 언제 쓰는지
- 단계별 명령/체크리스트
- 실수 방지 규칙

### schema

JSON, DB, payload 구조입니다.

필수 항목:

- 목적
- 현재 확정된 필드
- 아직 미정인 필드
- 생성/검증 TODO

확정 전에는 큰 JSON 예시를 문서에 박아두지 않습니다. LLM이 예시를 확정 스키마처럼 오해할 수 있기 때문입니다.

## Data Rules

- 대량 PDF는 Git에 넣지 않습니다.
- Drive/GCS의 원천 위치는 manifest에 기록합니다.
- 로컬 PDF는 `data/raw/pdfs/` 아래 캐시로만 둡니다.
- 추출 텍스트는 `data/raw/texts/` 또는 `data/processed/`에 둡니다.
- 실험 리포트와 SQLite는 Git에 넣지 않습니다.
- Git에 넣는 것은 문서, 스키마, 작은 manifest, 스크립트입니다.
- 실제 상담 데이터가 생기더라도 개인정보/발명 비밀이 들어갈 수 있으므로 Git에 넣지 않습니다.

## 중복 작성 기준

문서 간 중복은 완전히 금지하지 않습니다.

허용되는 중복:

- README나 index의 짧은 요약
- 팀원이 자주 보는 체크리스트
- 다른 문서로 안내하는 한 줄 설명

피해야 하는 중복:

- 같은 스키마 필드를 여러 문서에 길게 반복
- 확정되지 않은 JSON 예시를 여러 곳에 복사
- 파이프라인을 구현 완료처럼 여러 문서에 반복

원칙: **자세한 내용은 한 문서에만 두고, 다른 문서는 링크로 보냅니다.**

## Update Policy

새로운 결정이 생기면:

1. 관련 concept/schema/guide 문서를 수정합니다.
2. `index.md` 요약을 갱신합니다.
3. `log.md`에 날짜와 변경 파일을 남깁니다.
4. 팀원이 바로 실행해야 할 작업은 체크리스트로 씁니다.
