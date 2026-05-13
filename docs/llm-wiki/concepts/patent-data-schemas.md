---
title: Patent Data Schemas
created: 2026-05-12
updated: 2026-05-12
type: schema
tags: [schema, patent, consultation]
sources: []
confidence: medium
---

# Patent Data Schemas

## 한 줄 요약

PDF 원문, 가상 상담내역, 상담 에이전트 출력은 서로 다른 JSON으로 관리합니다.

아직 확정된 스키마가 적기 때문에, 이 문서는 **큰 JSON 예시를 고정하지 않고 각 JSON의 역할만 구분**합니다.

## 전체 관계

현재 개발 가정입니다. 구현 완료나 최종 파이프라인이 아닙니다.

```text
raw_reference_patent
→ patent_structure
→ simulated_consultation
→ invention_payload
→ agent_specific_payloads
```

## 1. patent_structure

PDF/TXT에서 추출해서 만드는 구조화 JSON입니다.

현재는 JSON 파일을 만들되, 상세 필드는 추출기를 만들면서 조정합니다. 문서에 큰 예시 JSON을 박아두지 않습니다.

저장 위치:

```text
data/processed/patent_structures/{patent_id}.json
```

초기 포함 후보:

- patent_id
- source PDF/TXT 위치
- 발명의 명칭
- 요약
- 기술분야
- 배경기술
- 해결하려는 과제
- 해결수단
- 효과
- 청구항 목록
- 도면/부호 정보
- IPC/CPC
- 추출 품질 경고

## 2. simulated_consultation

특허 내용을 보고 만든 **가상 사용자 상담내역 JSON**입니다.

실제 사용자 상담 데이터 확보가 어렵기 때문에, 현재 개발과 테스트는 이 데이터를 중심으로 진행합니다.

저장 위치:

```text
data/processed/simulated_consultations/{consultation_id}.json
```

초기 포함 후보:

- consultation_id
- source_patent_id
- simulation_mode
- user_messages
- intentionally_missing_slots
- expected_followup_targets
- generation_notes

주의:

- 원문 명세서를 그대로 복붙하지 않습니다.
- “사용자가 실제로 말할 법한 상담 입력”에 가깝게 만듭니다.
- 상세 생성 규칙은 아직 미정입니다.

## 3. invention_payload

상담 에이전트가 만드는 canonical payload입니다. 현재 `invention_extraction_guide.md`와 `agents/consultation/agent_payloads.py`가 이 구조를 기준으로 합니다.

이 부분은 실제 코드와 연결되어 있으므로 현재 문서에 구조를 남깁니다.

```json
{
  "payload_id": "",
  "created_at": "",
  "metadata": {
    "schema_version": "1.0",
    "source_type": "consultation_agent|simulated_consultation|uploaded_patent",
    "extracted_at": ""
  },
  "db_payload": {
    "consulting": {
      "user_id": "",
      "consultation_idx": 1,
      "raw_chat_log": [],
      "uploaded_file_path": "",
      "summary_problem": "",
      "summary_solution": "",
      "summary_difference": "",
      "summary_effect": ""
    },
    "algorithm_steps": [],
    "detail_elements": []
  },
  "extended_info": {
    "overall_flow": {
      "value": ""
    }
  },
  "traceability": {},
  "missing_information": [],
  "validation_rules": {}
}
```

## 4. agent_specific_payloads

후속 에이전트별 입력 JSON입니다.

예상 후속 에이전트:

- 선행기술조사 에이전트
- 청구항 작성 에이전트
- 도면/부호 정리 에이전트
- 발명의 설명 작성 에이전트
- 최종 문서 합치기 에이전트

원칙:

- 원본은 `invention_payload` 하나로 둡니다.
- 후속 에이전트 입력은 가능하면 규칙 기반 변환/Pydantic validation으로 만듭니다.
- 스키마가 확정되기 전에는 큰 JSON 예시를 문서에 복사하지 않습니다.

## 필수 검증 규칙

TODO: 아직 비워둡니다. 품질 기준이 정해지면 여기에 추가합니다.

## 관련 문서

- [[data-management-strategy]]
- [[pilot-600-v1]]
- [[pipeline-and-evaluation]]
- [[agent-architecture-notes]]
