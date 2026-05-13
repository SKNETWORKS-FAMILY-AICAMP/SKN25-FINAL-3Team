---
title: LLM Wiki Beginner Guide
created: 2026-05-12
updated: 2026-05-12
type: guide
tags: [collaboration, data]
sources: []
confidence: high
---

# LLM Wiki Beginner Guide

## 한 줄 요약

LLM Wiki는 팀원이 같이 보는 **프로젝트 설명서 폴더**입니다. 어렵게 생각하지 말고, GitHub에 올라가는 Markdown 문서 모음이라고 보면 됩니다.

## 왜 쓰는가

프로젝트 초반에는 말로 정한 내용이 금방 사라집니다.

LLM Wiki에는 다음을 남깁니다.

- 데이터가 어디 있는지
- 어떤 JSON을 만들기로 했는지
- 아직 미정인 부분이 뭔지
- 다음 작업이 뭔지
- 팀원이 실수하면 안 되는 규칙이 뭔지

## 파일별 역할

| 파일/폴더 | 역할 | 처음 보는 사람 필독? |
|---|---|---|
| `README.md` | LLM Wiki 시작 문서 | 예 |
| `index.md` | 전체 목차 | 예 |
| `SCHEMA.md` | 문서 작성 규칙 | 문서 수정할 때만 |
| `log.md` | 작업 기록 | 아니오 |
| `concepts/` | 개념/전략/설계 메모 | 필요한 것만 |
| `raw/` | 원천 자료 기록 | 필요할 때만 |

## 문서 읽는 순서

처음 온 팀원은 이 순서만 보면 됩니다.

1. `docs/llm-wiki/README.md`
2. `docs/llm-wiki/index.md`
3. `docs/llm-wiki/concepts/team-collaboration-guide.md`
4. `docs/llm-wiki/concepts/data-management-strategy.md`
5. 필요한 작업과 관련된 concept 문서

## YAML frontmatter 쉽게 설명

Markdown 맨 위의 이런 부분입니다.

```yaml
---
title: Example
created: 2026-05-12
updated: 2026-05-12
type: concept
tags: [data]
sources: []
confidence: medium
---
```

사람이 읽는 본문은 아니고, 문서의 이름표입니다.

- `title`: 문서 제목
- `created`: 만든 날짜
- `updated`: 마지막 수정 날짜
- `type`: 문서 종류
- `tags`: 주제 태그
- `sources`: 참고한 원천 자료
- `confidence`: 확실한 정도

팀원이 새 문서를 만들 때는 기존 문서를 복사해서 위쪽만 바꾸면 됩니다.

## wiki link란?

문서끼리 연결하는 링크입니다.

```md
[[data-management-strategy]]
```

Obsidian에서는 클릭 가능한 링크처럼 보입니다. GitHub에서는 일반 텍스트처럼 보일 수 있지만, LLM이 문서 관계를 이해하는 데 도움이 됩니다.

## manifest 쉽게 설명

manifest는 데이터 파일 목록표입니다.

예를 들어 “600건 중 어떤 PDF를 쓰는지, Drive 파일 ID가 뭔지, 로컬에 어디 받는지”를 적은 장부입니다.

PDF를 Git에 직접 올리지 않고도 팀원이 같은 파일을 찾을 수 있게 해줍니다.

## 중복은 괜찮은가?

짧은 요약 중복은 괜찮습니다.

예:

- README에 한 줄 요약
- index에 한 줄 요약
- 실제 자세한 설명은 concept 문서 하나에만 작성

피해야 할 것은 긴 JSON 예시나 확정 안 된 스키마를 여러 문서에 복사하는 것입니다.

## 문서 쓸 때 원칙

- 확정된 것과 예정인 것을 구분합니다.
- 아직 모르면 `TODO`라고 씁니다.
- 긴 JSON 예시는 확정 전까지 많이 넣지 않습니다.
- 자세한 내용은 한 문서에만 두고, 다른 곳에서는 링크만 겁니다.
- 변경하면 `log.md`에 짧게 기록합니다.

## 관련 문서

- [[developer-workflow-scenario]]
- [[data-management-strategy]]
- [[patent-data-schemas]]
- [[team-collaboration-guide]]
- [[agent-architecture-notes]]
