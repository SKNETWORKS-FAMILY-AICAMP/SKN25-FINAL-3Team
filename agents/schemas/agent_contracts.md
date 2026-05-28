# Agent Contracts

중간발표 MVP는 복잡한 분기/순환 LangGraph가 아니라 **고정 단방향 파이프라인**으로 구현한다.

```text
5개 입력 → Summary Agent(요약본작성) → 사용자 확인/피드백 → 청구항 → 도면 → 선행기술 → 명세서 → Composer → 최종 출력
```

## 공통 규칙

- 모든 agent input은 `PatentAgentState` 하나로 통일한다.
- 모든 agent output은 `agents/schemas/`의 담당 Pydantic schema에 맞춘다.
- 팀원 agent는 내부 구현이 자유롭고, 마지막에 dict를 반환해도 된다.
- Master/Graph가 raw output을 검증한 뒤 `model_dump()` 결과만 state에 merge한다.
- Master/Composer가 읽는 최소 필드만 고정한다.
- 추가 정보는 `summary`, `notes`, `evidence`, `warnings`, `details`에 넣는다.
- LLM raw output을 state에 직접 넣지 않는다.
- 별도 전달 객체를 새로 만들지 않고, LangGraph shared state의 `summary.structured_invention`을 후속 agent가 읽는다.

## Master Agent 범위

중간발표용 Master는 지능형 라우터가 아니라 **고정 파이프라인 실행 관리자**다.

하는 일:

1. 5개 입력값 존재 여부 확인
2. Summary Agent 호출
3. 요약본을 사용자에게 보여주고 승인/피드백 상태 관리
4. 피드백이 있으면 Summary Agent 재호출
5. 승인되면 `DEFAULT_PIPELINE`을 순서대로 실행
6. 각 agent output을 Pydantic 검증 후 state에 저장

하지 않는 일:

- 입력 내용에 따라 agent를 동적으로 생략/추가
- claim/prior_art/drawing 실행 순서 판단
- Review 결과 기반 자동 재실행
- 복잡한 LangGraph conditional routing

```python
DEFAULT_PIPELINE = (
    "summary",
    "claim",
    "drawing",
    "prior_art",
    "specification",
    "composer",
)
```

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

## 모든 Agent 공통 output 필드

모든 agent output schema는 `AgentOutputBase`를 상속한다.

위치:

```text
agents/schemas/common.py
```

공통 필드:

| 필드 | 타입 | 의미 |
|---|---|---|
| `status` | `"ok" / "needs_user_input" / "failed"` | agent 실행 결과 상태 |
| `summary` | `str` | 사람이 보는 짧은 결과 요약 |
| `warnings` | `list[str]` | 검토 필요/불확실/누락 경고 |
| `notes` | `list[str]` | agent 내부 판단 또는 보조 메모 |
| `evidence` | `list[EvidenceItem]` | 근거 조각. source/text/path/score 포함 가능 |
| `details` | `dict[str, Any]` | 담당 agent별 추가 정보 |

따라서 팀원 agent는 최소한 아래 형태를 반환할 수 있다.

```python
{
    "status": "ok",
    "summary": "청구항 초안 5개를 생성했습니다.",
    "warnings": [],
    "notes": [],
    "evidence": [],
    "details": {},
    # 아래에는 자기 담당 schema 필드 추가
}
```

단, 각 agent별 필수/최소 필드는 아래 계약을 따른다.

## Agent별 최소 계약

### Master Agent

- 입력: `PatentAgentState`
- 출력: `MasterAgentOutput`
- 저장 위치: 필요 시 `state["workflow"]`/trace에 반영
- 최소 필드: `stage`, `action`, `current_agent`, `next_agent`, `pipeline_index`, `summary_accepted`, `feedback_required`, `route_reason`
- 중간발표에서는 고정 pipeline 실행 상태만 관리한다.

### Summary Agent

- 입력: `PatentAgentState` 또는 `InventorInput`
- 출력: `SummaryAgentOutput`
- 저장 위치: `state["summary"]`
- 후속 agent가 가장 먼저 읽어야 하는 위치: `state["summary"]["structured_invention"]`
- 역할: 5개 발명 입력을 사람이 읽을 요약본과 후속 agent용 구조화 발명 정보로 변환한다.
- 주의: Summary Agent는 재질문/slot filling/청구항 작성 agent가 아니다. 부족한 정보는 `missing_slots`, `clarification_questions`, `warnings`에 남긴다.

#### Summary Agent 입력 5개 필드

| 필드 | 의미 | 비고 |
|---|---|---|
| `project_name` | 프로젝트명 또는 발명 명칭 후보 | 최종 명칭은 후속 agent/composer에서 조정 가능 |
| `problem_to_solve` | 해결하고자 하는 문제/과제 | 선행기술·명세서·청구항의 출발점 |
| `prior_art_problem` | 기존 기술의 문제점 | 비어 있으면 `warnings`에 기록 |
| `core_technology` | 핵심 기술 구성/해결 수단 | components/process_steps 추출의 주 근거 |
| `expected_effect` | 발명의 효과 | 명세서 `발명의 효과` 작성 재료 |

#### `state["summary"]` 최상위 반환 필드

| 필드 | 타입 | 후속 사용처 |
|---|---|---|
| `status` | `ok / needs_user_input / failed` | Master/Graph 실행 상태 판단 |
| `summary` | `str` | 짧은 실행 요약 |
| `warnings` | `list[str]` | 모든 후속 agent가 검토해야 할 불확실성 |
| `notes` | `list[str]` | 보조 메모 |
| `evidence` | `list[EvidenceItem]` | 입력 근거 조각이 있을 때 사용 |
| `details` | `dict` | 모델명, token usage, regex pre-analysis 등 디버깅/추적 정보 |
| `project_name` | `str` | 원 입력 보존 |
| `problem_to_solve` | `str` | 원 입력 보존 |
| `prior_art_problem` | `str` | 원 입력 보존 |
| `core_technology` | `str` | 원 입력 보존 |
| `expected_effect` | `str` | 원 입력 보존 |
| `readable_summary` | `str` | 사용자 확인용 요약본 |
| `structured_invention` | `dict` | 후속 agent 공통 입력 |
| `feedback_applied` | `list[str]` | 사용자 피드백 반영 내역 |

#### `structured_invention` 반환 필드

| 필드 | 타입 | 읽는 agent | 의미 |
|---|---|---|---|
| `title` | `str` | Claim/Drawing/Specification/Composer | 발명 명칭 후보 |
| `technical_field_natural` | `str` | Specification/PriorArt | IPC 코드가 아닌 자연어 기술분야 |
| `background` | `list[str]` | Specification/PriorArt | 사용 맥락/배경기술 후보 |
| `use_cases` | `list[str]` | Specification/Drawing | 적용 사례 |
| `problem` | `str` | Claim/PriorArt/Specification | 해결하려는 문제 |
| `prior_art_problem` | `str` | PriorArt/Specification | 기존 기술 문제점 |
| `solution` | `str` | Claim/Drawing/Specification | 핵심 해결수단 |
| `components` | `list[SummaryComponent]` | Claim/Drawing/Specification | 구성요소 후보 |
| `process_steps` | `list[SummaryProcessStep]` | Claim/Drawing/Specification | 방법 단계/흐름도 후보 |
| `input_data` | `list[str]` | Claim/Drawing/PriorArt | 입력 데이터/요청/신호 |
| `output_result` | `list[str]` | Claim/Drawing/PriorArt | 출력 결과/생성물 |
| `technical_features` | `list[str]` | Claim/PriorArt/Specification | 기술적 특징 |
| `differentiators` | `list[str]` | Claim/PriorArt | 차별점/권리화 포인트 후보 |
| `expected_effects` | `list[str]` | Specification/Composer | 단순 효과 목록 |
| `effects` | `list[SummaryEffect]` | Specification/Composer | 원인-효과-관련요소 구조 |
| `missing_slots` | `list[str]` | Master/Review | 부족한 정보 항목 |
| `clarification_questions` | `list[str]` | Master/Review | 사용자 추가 질문 후보 |
| `term_registry_seed` | `list[TermCandidate]` | Drawing/Composer/DocumentLinks | 용어 통일 초기 후보 |
| `application_domain` | `str` | PriorArt | 적용 분야 |
| `ai_techniques` | `list[str]` | PriorArt/Claim | AI/소프트웨어 기술 키워드 |

#### 하위 객체 구조

```python
SummaryComponent = {
    "name": str,
    "role": str,
    "effect": str,
    "related_inputs": list[str],
    "related_outputs": list[str],
    "evidence": str,
}

SummaryProcessStep = {
    "order": int,
    "name": str,
    "description": str,
    "input_data": list[str],
    "output_data": list[str],
}

SummaryEffect = {
    "effect": str,
    "cause": str,
    "related_elements": list[str],
    "evidence": str,
}

TermCandidate = {
    "id": str,
    "canonical_name": str,
    "aliases": list[str],
    "source": str,
}
```

#### 후속 agent별 사용 가이드

| 후속 agent | 우선 읽을 필드 |
|---|---|
| Claim Agent | `problem`, `solution`, `components`, `process_steps`, `technical_features`, `differentiators`, `expected_effects` |
| Drawing Agent | `components`, `process_steps`, `input_data`, `output_result`, `term_registry_seed` |
| Prior Art Agent | `problem`, `prior_art_problem`, `solution`, `technical_features`, `differentiators`, `application_domain`, `ai_techniques` |
| Specification Agent | `readable_summary`, `technical_field_natural`, `background`, `problem`, `solution`, `components`, `process_steps`, `effects`, `expected_effects`, `use_cases` |
| Composer Agent | `readable_summary`, `structured_invention`, `warnings`, `term_registry_seed` |

#### 최소 예시

```python
state["summary"] = {
    "status": "ok",
    "summary": "요약본작성 완료",
    "warnings": ["prior_art_problem 입력이 비어 있어 종래기술 대비 차별 과제는 제한적으로만 특정됨"],
    "notes": [],
    "evidence": [],
    "details": {"model": "gpt-5.4"},
    "project_name": "인스트럭션 기반 문서 자동 생성 방법 및 그 시스템",
    "problem_to_solve": "문서 작성 요청에 대해 제한된 지식 베이스를 검색하고 문서를 자동 작성",
    "prior_art_problem": "",
    "core_technology": "문서 작성 요청 수신, 검색 대상 획득, 지식 베이스 검색, 전처리 데이터 획득, LLM 입력, 초안 생성",
    "expected_effect": "문서 작성 리소스 검색 정확도 향상 및 리소스 외부 유출 방지",
    "readable_summary": "사용자 단말의 문서 작성 요청을 바탕으로 지식 베이스를 검색하고 LLM으로 문서 초안을 생성하는 기술이다.",
    "structured_invention": {
        "title": "인스트럭션 기반 문서 자동 생성 방법 및 그 시스템",
        "technical_field_natural": "검색 증강 생성 기반 문서 자동 생성 기술",
        "background": [],
        "use_cases": ["업무 문서 초안 생성", "제한된 사내 지식 기반 문서 작성"],
        "problem": "문서 작성에 필요한 리소스를 신속하고 정확하게 검색하고 자동 작성하는 문제",
        "prior_art_problem": "",
        "solution": "문서 작성 요청에서 검색 대상을 획득하고 지식 베이스 검색 결과를 전처리하여 LLM에 입력한다.",
        "components": [
            {"name": "문서 작성 시스템", "role": "요청 처리와 문서 초안 생성을 수행", "effect": "문서 작성 자동화", "related_inputs": ["문서 작성 요청"], "related_outputs": ["초안 콘텐츠"], "evidence": "문서 작성 시스템은 서비스 서버와 지식 베이스를 포함"}
        ],
        "process_steps": [
            {"order": 1, "name": "문서 작성 요청 수신", "description": "사용자 단말로부터 제1 문서 작성 요청을 수신", "input_data": ["문서 작성 요청"], "output_data": ["요청 정보"]}
        ],
        "input_data": ["문서 작성 요청", "업로드 리소스"],
        "output_result": ["초안 콘텐츠", "문서 전처리 데이터"],
        "technical_features": ["요청 기반 검색 대상 추출", "지식 베이스 검색", "LLM 기반 초안 생성"],
        "differentiators": ["검색 결과를 전처리 데이터로 변환해 LLM 입력에 사용"],
        "expected_effects": ["문서 작성 리소스 검색 정확도 향상"],
        "effects": [
            {"effect": "문서 작성 효율 향상", "cause": "검색 결과와 전처리 데이터를 LLM 입력으로 사용", "related_elements": ["지식 베이스", "LLM 서버"], "evidence": "검색된 자료에 기초하여 문서를 자동 작성"}
        ],
        "missing_slots": ["종래기술 문제점"],
        "clarification_questions": ["기존 문서 작성 도구와 비교한 가장 큰 차별점은 무엇인가?"],
        "term_registry_seed": [
            {"id": "T001", "canonical_name": "문서 작성 시스템", "aliases": ["서비스 서버"], "source": "core_technology"}
        ],
        "application_domain": "문서 자동 생성",
        "ai_techniques": ["LLM", "RAG"]
    },
    "feedback_applied": []
}
```

#### 중요 원칙

- 후속 agent는 별도 전달 객체를 새로 만들지 말고 `state["summary"]["structured_invention"]`을 읽는다.
- `components`, `process_steps`는 Summary 단계 후보이다. 최종 청구항 구성요소/도면 참조부호는 Claim/Drawing Agent가 확정한다.
- `effects`는 단순 홍보 문구가 아니라 명세서 작성용 원인-효과 구조이다.
- `term_registry_seed`는 완성된 용어 사전이 아니라 Composer/DocumentLinks가 보강할 초기 후보이다.
- `warnings`는 무시하지 않는다. 선행기술/청구항/명세서 agent는 경고를 보고 권리범위 과확장이나 허위 구체화를 피해야 한다.

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
- 최소 필드: `status`, `summary`, `warnings`, `notes`, `evidence`, `details`, `title`, `abstract`, `sections`, `claims`, `drawings`, `specification`, `prior_art_report`, `rendered_markdown`, `rendered_docx_path`, `rendered_html_path`, `unresolved_items`, `composer_notes`
- Composer는 부족한 내용을 발명하지 않고, 각 agent 결과를 최종 문서 형태로 정리한다.
- `run_composer_agent(state)`는 실제 `.docx`를 생성하고, `final_package` 형태의 dict를 반환한다.
- `graph.py`는 `safe_validate_output()`를 통해 Composer raw output을 검증한 뒤 `state["final_package"]`에 저장한다.

## 구현 파일 역할

- `agents/schemas/master.py`: 중간발표용 Master 진행 상태/action 계약.
- `agents/schemas/summary.py`: 5개 입력, readable summary, structured invention 계약.
- `agents/schemas/`: 나머지 agent별 최소 output 계약.
- `agents/repair.py`: LLM repair prompt/API 호출. 형식 정규화 전용.
- `agents/validation.py`: validate → repair once → validate again → hard fallback 공통 함수.
- `agents/graph.py`: 중간발표용 단방향 실행 skeleton. 나중에 LangGraph `StateGraph`로 옮길 수 있는 연결 통로.
- `agents/state.py`: shared state의 큰 그릇. 실제 output 검증은 schema/validation에서 처리한다.
