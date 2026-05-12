# 사용자 발명 설명 → 구조화 JSON + 부족정보 질문 추출 기준 문서

## 1. 목적

이 문서는 사용자의 자유로운 발명 설명 또는 업로드된 특허 자료를 입력받아, 특허 상담 에이전트가 어떤 정보를 최소한으로 추출해야 하는지 정의한다.

최종 출력은 다음 두 가지다.

1. 구조화된 `invention.json`
2. 부족하거나 불명확한 정보에 대한 후속 질문 목록

이 문서는 특정 예시 특허 하나에 맞춘 하드코딩 규칙이 아니라, 소프트웨어, 하드웨어, 화학, BM, 플랫폼 서비스 등 다양한 발명에 적용 가능한 공통 추출 기준을 목표로 한다.

---

## 2. 전체 처리 흐름

```text
사용자 발명 설명 또는 특허 자료
        ↓
원문 보존(raw_chat_log / file_text)
        ↓
핵심 정보 추출
        ↓
DB 저장 가능 정보와 상담 보조 정보 분리
        ↓
출처 추적 정보 기록
        ↓
부족 정보 탐지
        ↓
후속 질문 생성
        ↓
invention.json 생성
        ↓
db_payload만 DB 저장
```

---

## 3. 최종 JSON 구조

```json
{
  "metadata": {},
  "db_payload": {
    "consulting": {},
    "algorithm_steps": [],
    "detail_elements": []
  },
  "extended_info": {},
  "traceability": {},
  "missing_information": [],
  "validation_rules": {}
}
```

---

## 4. 각 섹션의 역할

### 4.1 metadata

자료의 출처와 추출 환경을 기록한다.

필수 권장 항목:

- `schema_version`
- `source_type`
- `source_file`
- `extraction_mode`
- `extracted_at`
- `language`

특허 자료를 사용하는 경우 추가 가능 항목:

- `patent_info.title`
- `patent_info.registration_number`
- `patent_info.application_number`
- `patent_info.claim_count`

주의: `metadata`는 DB 저장 대상이 아니라 추적 및 관리용이다.

---

### 4.2 db_payload

현재 DB에 직접 저장 가능한 정보만 넣는다.

#### consulting

현재 DB 컬럼과 1:1로 대응한다.

| JSON 필드 | DB 컬럼 | 설명 |
|---|---|---|
| `user_id` | `consulting.user_id` | 발명가 식별자 |
| `consultation_idx` | `consulting.consultation_idx` | 상담 회차 |
| `raw_chat_log` | `consulting.raw_chat_log` | 상담 전체 원문 |
| `uploaded_file_path` | `consulting.uploaded_file_path` | 업로드 파일 경로 |
| `summary_problem` | `consulting.summary_problem` | 기존 기술의 문제점 |
| `summary_solution` | `consulting.summary_solution` | 핵심 해결 수단 |
| `summary_difference` | `consulting.summary_difference` | 기존 기술 대비 차별성 |
| `summary_effect` | `consulting.summary_effect` | 기대효과 |

#### algorithm_steps

청구항 1 또는 핵심 방법 발명의 순서 정보를 저장한다.

| JSON 필드 | DB 컬럼 | 설명 |
|---|---|---|
| `step_seq` | `algorithm_steps.step_seq` | 단계 순서 |
| `step_content` | `algorithm_steps.step_content` | 단계 내용 |

권장 기준:

- 최소 3단계 이상
- 최대 10단계 이하
- 단계는 실행 순서가 드러나야 함
- 단순 설명이 아니라 동작 또는 처리 단위여야 함

#### detail_elements

종속항 소재를 저장한다.

| element_type | 의미 | 예시 |
|---|---|---|
| `implementation` | 구체적 구현 수단 | 센서, 모듈, API, 모델, 장치 |
| `parameter` | 데이터 파라미터/포맷 | ID, 수치, 임계값, 데이터 형식 |
| `algorithm` | 핵심 로직/수식 | 스코어링, 분류, 임베딩, 제어 로직 |
| `optional` | 부가 기능 | 알림, 연동, 선택 UI |
| `error_handling` | 예외 처리 | 실패 시 재시도, 수동 입력, 대체 경로 |

주의: `db_payload` 안에는 현재 DB 컬럼에 없는 값을 넣지 않는다.

---

## 5. extended_info

DB에는 직접 저장하지 않지만 상담 품질과 후속 에이전트에 유용한 정보를 둔다.

권장 항목:

- `overall_flow`
- `prior_art_or_existing_technology`
- `inventor_focus_point`
- `technical_field`
- `main_claim_summary`

주의:

- 이 섹션은 발명 분야에 따라 값이 비어 있을 수 있다.
- 특정 예시 특허에만 맞는 필드를 `db_payload`에 넣지 않는다.
- DB 저장이 필요해지면 나중에 별도 확장 테이블을 검토한다.

---

## 6. traceability

추적 가능성을 위해 각 추출값의 근거를 기록한다.

핵심 필드는 반드시 출처를 가져야 한다.

필수 추적 대상:

- `summary_problem`
- `summary_solution`
- `summary_difference`
- `summary_effect`
- `algorithm_steps`
- 주요 `detail_elements`
- `missing_information`의 판단 근거

권장 형식:

```json
{
  "db_payload.consulting.summary_problem": {
    "source_section": "배경기술",
    "source_text": "원문 근거 문장",
    "extraction_note": "왜 이 값을 추출했는지 설명"
  }
}
```

추적 가능성을 확보하면 다음 장점이 있다.

- 클로드 등 다른 모델과 비교 검토 가능
- 추출 오류 발생 시 원인 파악 가능
- 사용자가 왜 이런 질문을 받는지 확인 가능
- 특허 명세서 초안 생성 시 근거 기반 작성 가능

---

## 7. missing_information

부족하거나 불명확한 정보를 기록하고 후속 질문을 생성한다.

필수 필드:

| 필드 | 설명 |
|---|---|
| `field` | 부족한 정보 이름 |
| `status` | `missing`, `needs_clarification`, `weak_evidence` 등 |
| `reason` | 왜 부족하다고 판단했는지 |
| `question` | 사용자에게 물어볼 질문 |
| `priority` | high, medium, low |
| `source_basis` | 부족 판단의 근거 |

예시:

```json
{
  "field": "differentiation",
  "status": "needs_clarification",
  "reason": "기존 기술 대비 차별점이 일반적 효과 수준으로만 설명되어 있음",
  "question": "기존 제품이나 특허와 비교했을 때, 본 발명만의 가장 핵심적인 차별점은 무엇입니까?",
  "priority": "high"
}
```

---

## 8. 최소 필수 추출 항목

사용자 발명 설명에서 최소한 아래 정보는 확보해야 한다.

### 8.1 기존 문제점

질문 예시:

- 기존 기술이나 제품에서 어떤 불편함이 있었습니까?
- 사용자가 겪던 문제는 무엇입니까?
- 왜 이 발명이 필요했습니까?

DB 저장 위치:

- `db_payload.consulting.summary_problem`

---

### 8.2 해결 방법

질문 예시:

- 그 문제를 어떤 방식으로 해결합니까?
- 핵심 기술 수단은 무엇입니까?
- 시스템 또는 장치가 어떤 처리를 수행합니까?

DB 저장 위치:

- `db_payload.consulting.summary_solution`

---

### 8.3 기존 기술 대비 차별성

질문 예시:

- 기존 특허, 제품, 방식과 무엇이 다릅니까?
- 단순 개선이 아니라 새롭게 주장할 수 있는 부분은 무엇입니까?
- 경쟁 기술이 따라 하기 어려운 점은 무엇입니까?

DB 저장 위치:

- `db_payload.consulting.summary_difference`

---

### 8.4 기대효과

질문 예시:

- 이 발명으로 어떤 효과가 발생합니까?
- 시간, 비용, 정확도, 편의성, 안정성 중 어떤 부분이 좋아집니까?
- 사용자는 어떤 이익을 얻습니까?

DB 저장 위치:

- `db_payload.consulting.summary_effect`

---

### 8.5 작동 단계

질문 예시:

- 발명이 실제로 작동하는 순서를 3단계 이상으로 설명해 주실 수 있습니까?
- 입력부터 결과 출력까지 어떤 순서로 진행됩니까?
- 장치나 서버 내부에서 어떤 처리가 순차적으로 이루어집니까?

DB 저장 위치:

- `db_payload.algorithm_steps`

---

### 8.6 종속항 소재

질문 예시:

- 구체적인 구현 수단은 무엇입니까?
- 어떤 데이터나 파라미터를 사용합니까?
- 핵심 로직, 수식, 알고리즘이 있습니까?
- 선택적으로 추가될 수 있는 기능은 무엇입니까?
- 실패하거나 예외 상황일 때 어떻게 처리합니까?

DB 저장 위치:

- `db_payload.detail_elements`

---

## 9. 하드코딩 방지 규칙

특정 예시 하나에 맞춘 구조가 되지 않도록 다음 규칙을 지킨다.

1. `db_payload`에는 현재 DB 컬럼에 대응되는 값만 넣는다.
2. 예시 특허에서만 등장하는 고유 개념은 `extended_info`에 둔다.
3. 특정 기술명, 특정 알고리즘명, 특정 서비스명을 필수 필드로 만들지 않는다.
4. 모든 발명에 공통적인 추상 필드만 필수로 둔다.
5. 분야별 세부정보는 `detail_elements`의 타입으로 분류한다.
6. 값이 불명확하면 추측해서 채우지 말고 `missing_information`에 질문으로 남긴다.

---

## 10. 추적 가능성 규칙

1. 핵심 요약 4개는 반드시 출처를 남긴다.
2. 알고리즘 단계는 가능하면 청구항 또는 실시예 원문과 연결한다.
3. 종속항 소재도 가능하면 원문 섹션을 남긴다.
4. 부족 정보 질문은 반드시 `reason`과 `source_basis`를 포함한다.
5. 모델이 추론한 내용은 `extraction_note`에 추론임을 명시한다.

---

## 11. 품질 검증 체크리스트

최종 JSON 생성 후 아래를 확인한다.

- [ ] `db_payload`가 현재 DB 구조와 충돌하지 않는가?
- [ ] DB에 없는 필드가 `consulting` 안에 들어가지 않았는가?
- [ ] `summary_problem`, `summary_solution`, `summary_difference`, `summary_effect`가 모두 있는가?
- [ ] `algorithm_steps`가 최소 3단계 이상인가?
- [ ] `detail_elements`가 5가지 타입 중 하나로만 분류되었는가?
- [ ] 핵심 필드마다 `traceability`가 있는가?
- [ ] 부족한 정보가 질문 형태로 정리되었는가?
- [ ] 특정 예시 특허에만 맞춘 필드가 필수 구조로 들어가지 않았는가?

---

## 12. DB 저장 정책

현재 DB에는 `db_payload`만 저장한다.

```text
db_payload.consulting       → consulting 테이블
db_payload.algorithm_steps  → algorithm_steps 테이블
db_payload.detail_elements  → detail_elements 테이블
```

다음 항목은 현재 DB에 직접 저장하지 않는다.

```text
metadata
extended_info
traceability
missing_information
validation_rules
```

다만 필요하면 아래 방식 중 하나를 선택할 수 있다.

1. `raw_chat_log`에 함께 보존
2. JSON 파일로 별도 저장
3. 나중에 `consulting_extended` 같은 확장 테이블 설계

현재 단계에서는 DB 수정 없이 `invention.json`을 중간 구조체로 사용하는 것을 권장한다.
