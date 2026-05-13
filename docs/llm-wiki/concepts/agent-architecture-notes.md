---
title: Agent Architecture Notes
created: 2026-05-12
updated: 2026-05-12
type: concept
tags: [architecture, consultation, pipeline]
sources: []
confidence: medium
---

# Agent Architecture Notes

## 한 줄 요약

상담 에이전트와 후속 에이전트는 LangGraph/LangChain 기반의 그래프 상태 흐름으로 설계하는 방향입니다. 아직 구현 확정안은 아닙니다.

## 현재 가정

- 상담 흐름은 단순 프롬프트 1회 호출보다 **state graph**로 관리합니다.
- 각 단계는 LangGraph node 또는 LangChain runnable 형태로 쪼갭니다.
- 초기에 라우터는 별도 에이전트로 분리하지 않고, 마스터/상담 흐름 내부 조건 분기로 둘 수 있습니다.
- 후속 에이전트 입력은 `invention_payload`에서 규칙 기반으로 파생하는 것을 우선합니다.
- 스키마가 흔들릴 때만 LLM을 추가로 써서 요약/복구를 검토합니다.

## 초기 노드 후보

아직 구현 완료가 아니라 설계 후보입니다.

```text
user_input
→ intake_node
→ completeness_check_node
→ followup_question_node
→ invention_payload_node
→ human_review_node
→ downstream_payload_mapper
```

## 상담 에이전트에서 중요한 상태

- raw_chat_log
- extracted_problem
- extracted_solution
- extracted_difference
- extracted_effect
- missing_information
- followup_questions
- invention_payload
- review_status

## 후속 에이전트 후보

```text
invention_payload
→ prior_art_search_payload
→ claim_drafting_payload
→ drawing_payload
→ specification_payload
→ package_assembly
```

## 현재 주의사항

- 이 문서는 구현 완료 문서가 아닙니다.
- `patent_structure`, `simulated_consultation`, `invention_payload`의 경계가 먼저 잡혀야 합니다.
- LangGraph node 이름과 state schema는 구현하면서 바뀔 수 있습니다.
- 확정된 내용만 코드와 README에 반영합니다.

## 관련 문서

- [[patent-data-schemas]]
- [[data-management-strategy]]
- [[pipeline-and-evaluation]]
