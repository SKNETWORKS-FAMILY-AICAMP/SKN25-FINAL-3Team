# Agent Contracts

중간발표 MVP는 복잡한 분기/순환 LangGraph가 아니라 단방향 파이프라인으로 구현한다.

```text
입력 → 상담 → 청구항 → 도면/선행기술/명세서 → Composer → 최종 출력
```

## 공통 규칙

- 모든 agent input은 `PatentAgentState` 하나로 통일한다.
- 모든 agent output은 `agents/schemas/`의 담당 Pydantic schema에 맞춘다.
- 팀원 agent는 내부 구현이 자유롭고, 마지막에 dict를 반환해도 된다.
- Master/Graph가 raw output을 검증한 뒤 `model_dump()` 결과만 state에 merge한다.
- Master/Composer가 읽는 최소 필드만 고정한다.
- 추가 정보는 `summary`, `notes`, `evidence`, `warnings`, `details`에 넣는다.
- LLM raw output을 state에 직접 넣지 않는다.

## Validation / Repair / Hard Fallback

각 agent output 처리 순서:

```text
raw_output
→ Pydantic validate
→ 실패 시 LLM repair 1회
→ repair 결과 재검증
→ 그래도 실패하면 hard fallback
→ 검증 통과한 model_dump()만 state 저장
```

Repair LLM은 review agent가 아니다. 새 특허 내용을 만들거나 품질을 개선하지 않고, raw output 안의 내용을 schema 필드에 맞게 옮기는 역할만 한다.

Repair prompt 핵심 문장:

```text
이 output은 {agent_name} agent 결과다.
최종적으로 {schema_name} schema에 맞아야 한다.
raw_output 안에 있는 내용을 버리지 말고 필드에 맞게 옮겨라.
없는 내용은 만들지 말고 빈 값으로 둬라.
품질 개선이나 새 특허 내용 생성은 하지 마라.
JSON object 하나만 반환하고 설명/Markdown/code block은 출력하지 마라.
```

Repair에 넘기는 정보:

- `agent_name`
- `schema_name`
- `schema.model_json_schema()`
- Pydantic `validation_errors`
- `raw_output`

Hard fallback은 repair도 실패했을 때 쓰는 미리 정의된 빈/기본 결과다. 목적은 좋은 결과 생성이 아니라 데모 파이프라인이 죽지 않게 하는 것이다.

## Agent별 최소 계약

### Consultation Agent

- 입력: `PatentAgentState`
- 출력: `ConsultationAgentOutput`
- 저장 위치: `state["consultation"]`
- 최소 필드: `problem`, `solution`, `components`, `input_data`, `output_result`, `effects`, `differentiators`, `missing_slots`, `followup_questions`

### Claim Agent

- 입력: `PatentAgentState`
- 출력: `ClaimAgentOutput`
- 저장 위치: `state["claims"]`
- 최소 필드: `claim_plan`, `draft_claims`, `independent_claim_numbers`, `dependent_claim_numbers`, `claim_strategy_notes`
- `ClaimDraft.category`는 중간발표 기준 `method | system | storage_medium | unknown`만 사용한다.
- 종속항은 `depends_on`이 있어야 한다.

### Drawing Agent

- 입력: `PatentAgentState`
- 출력: `DrawingAgentOutput`
- 저장 위치: `state["drawings"]`
- 최소 필드: `figures`, `reference_numerals`, `drawing_notes`
- 구현: `agents/drawing/drawing_node.py` → `drawing_node(state)`
- 실패 시 fallback: `status="failed"`, `figures=[]`, `reference_numerals=[]`, `drawing_notes=[]`

**입력 예시 (state["consultation"] 또는 state["summary"]["structured_invention"])**

```json
{
  "consultation": {
    "invention_title": "스마트 재고 관리 시스템",
    "problem": "수작업 재고 집계로 인한 오류와 지연",
    "solution": "IoT 센서와 AI 예측 모델을 결합한 자동 재고 추적",
    "components": [
      {"name": "IoT 센서 모듈", "role": "실시간 재고 수량 감지"},
      {"name": "AI 예측 엔진", "role": "소비 패턴 분석 및 발주 예측"},
      {"name": "중앙 관리 서버", "role": "데이터 수집·처리·저장"}
    ],
    "process_steps": [
      {"order": 1, "name": "센서 데이터 수집", "description": "각 진열대 IoT 센서가 수량 변화 감지"},
      {"order": 2, "name": "AI 분석", "description": "수집 데이터를 AI 모델로 분석"},
      {"order": 3, "name": "알림 발송", "description": "임계치 도달 시 담당자에게 자동 알림"}
    ]
  }
}
```

**정상 출력 예시 (state["drawings"])**

```json
{
  "status": "ok",
  "summary": "도면 2개 생성 완료 (평균 82점)",
  "figures": [
    {
      "fig_no": "1",
      "title": "스마트 재고 관리 시스템 구성도",
      "type": "system_architecture",
      "components": ["IoT 센서 모듈", "AI 예측 엔진", "중앙 관리 서버"],
      "description": "전체 시스템 블록 구성도"
    },
    {
      "fig_no": "2",
      "title": "재고 관리 처리 흐름도",
      "type": "flowchart",
      "components": ["센서 데이터 수집", "AI 분석", "알림 발송"],
      "description": "데이터 처리 흐름도"
    }
  ],
  "reference_numerals": [
    {"number": "100", "label": "IoT 센서 모듈", "description": "실시간 재고 수량 감지", "component_id": "100"},
    {"number": "110", "label": "AI 예측 엔진", "description": "소비 패턴 분석 및 발주 예측", "component_id": "110"},
    {"number": "120", "label": "중앙 관리 서버", "description": "데이터 수집·처리·저장", "component_id": "120"}
  ],
  "drawing_notes": [
    "총 2개 도면 생성",
    "평균 품질 점수: 82.0점",
    "참조부호 3개"
  ],
  "warnings": [],
  "notes": [],
  "evidence": [],
  "details": {}
}
```

**실패 시 fallback 출력**

```json
{
  "status": "failed",
  "summary": "도면 생성 실패 — hard fallback",
  "figures": [],
  "reference_numerals": [],
  "drawing_notes": [],
  "warnings": ["발명 데이터 없음"],
  "notes": [],
  "evidence": [],
  "details": {}
}
```

### Prior Art Agent

- 입력: `PatentAgentState`
- 출력: `PriorArtAgentOutput`
- 저장 위치: `state["prior_art"]`
- 최소 필드: `query`, `candidates`, `overlap_points`, `difference_points`, `limitations`
- 후보에는 최소 `patent_id`, `title`, `score`, `matched_points`, `difference_points`, `evidence`, `pdf_path`를 둔다.

### Specification Agent

- 입력: `PatentAgentState`
- 출력: `SpecificationAgentOutput`
- 저장 위치: `state["specification"]`
- 최소 필드: `technical_field`, `background_art`, `problem_to_solve`, `means_for_solving`, `effects`, `brief_description_of_drawings`, `detailed_description`
- 구현: `agents/specification/specification_node.py` → `specification_node(state)`
- 실패 시 fallback: 모든 str 필드 `""`, `status="failed"`

**정상 출력 예시 (state["specification"])**

```json
{
  "status": "ok",
  "summary": "발명의 설명 초안 생성 완료",
  "technical_field": "본 발명은 IoT 센서와 AI를 결합한 스마트 재고 관리 시스템에 관한 것이다.",
  "background_art": "종래의 재고 관리는 수작업 집계에 의존하여 오류와 지연이 발생하였다.",
  "problem_to_solve": "수작업 재고 집계로 인한 오류·지연을 해소하고 실시간 재고 파악을 가능하게 한다.",
  "means_for_solving": "IoT 센서 모듈(100)이 실시간으로 재고 수량을 감지하고, AI 예측 엔진(110)이 소비 패턴을 분석하여 자동 발주를 수행한다.",
  "effects": "재고 관리 오류율을 90% 감소시키고, 발주 리드타임을 단축한다.",
  "brief_description_of_drawings": "도 1은 스마트 재고 관리 시스템의 전체 구성도이다.\n도 2는 재고 관리 처리 흐름도이다.",
  "detailed_description": "이하, 첨부된 도면을 참조하여 본 발명의 실시예를 상세히 설명한다...",
  "warnings": [],
  "notes": [],
  "evidence": [],
  "details": {}
}
```

### Composer Agent

- 입력: `PatentAgentState`
- 출력: `ComposerAgentOutput`
- 저장 위치: `state["final_package"]`
- 최소 필드: `title`, `abstract`, `sections`, `rendered_markdown`, `rendered_html_path`, `unresolved_items`
- Composer는 부족한 내용을 발명하지 않고, 각 agent 결과를 최종 문서 형태로 정리한다.

## 구현 파일 역할

- `agents/schemas/`: agent별 최소 output 계약.
- `agents/repair.py`: LLM repair prompt/API 호출. 형식 정규화 전용.
- `agents/validation.py`: validate → repair once → validate again → hard fallback 공통 함수.
- `agents/graph.py`: 중간발표용 단방향 실행 skeleton. 나중에 LangGraph `StateGraph`로 옮길 수 있는 연결 통로.
- `agents/state.py`: shared state의 큰 그릇. 현재 구조는 유지하고, 실제 output 검증은 schema/validation에서 처리한다.
