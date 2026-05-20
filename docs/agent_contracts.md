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
