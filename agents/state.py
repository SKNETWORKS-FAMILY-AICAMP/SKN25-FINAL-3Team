"""특허 멀티 에이전트용 LangGraph 공유 State 스키마.

이 파일은 실제 기능 구현 파일이라기보다, 여러 에이전트가 서로 주고받을
공통 JSON 구조를 정의하는 설계도에 가깝다.

핵심 설계 의도:
- 각 에이전트 산출물은 자유 텍스트만 두지 말고 구조화된 JSON으로 저장한다.
- `document_links`는 "상기", "전술한", "도 1", "(120)", "제1항"처럼
  특허 문서 내부에서 서로를 참조하는 관계를 저장한다.
- `invention_graph`는 발명의 구성요소/데이터 흐름/관계를 저장한다.
  여기서 graph는 ReAct의 숨은 추론 과정이 아니라, 에이전트들이 공유할
  발명 구조 JSON이다.
- 고정 문체/작성 규칙은 `rules/*.yaml`에 두고, 이번 실행에서 바뀌는 옵션만
  `drafting_options`에 저장한다.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

# -----------------------------------------------------------------------------
# 1. 공통 분류값
# -----------------------------------------------------------------------------
# Literal은 "이 값들 중 하나만 허용한다"는 뜻이다.
# 예: AgentName은 "master", "consultation" 등 정해진 agent 이름만 가질 수 있다.

# 그래프에 참여하는 에이전트 이름 목록.
AgentName = Literal[
    "master",  # 전체 흐름을 제어하는 Orchestrator. 직접 문서 작성보다는 다음 agent 선택 담당.
    "consultation",  # 상담 agent. 사용자 설명을 발명 구조 JSON으로 정리하고 부족 정보를 질문.
    "prior_art",  # 선행기술조사 agent. 유사 특허 검색, 차이점, 신규성/진보성 리스크 분석.
    "claim",  # 청구항 생성 agent. 청구항 설계도와 독립항/종속항 초안 생성.
    "drawing",  # 도면 agent. 도면 구성, 도 번호, 참조부호 계획 생성.
    "specification",  # 발명의 설명 agent. 기술분야/배경기술/효과/상세설명 초안 생성.
    "composer",  # 명세서 병합 agent. 상담/청구항/도면/설명 결과를 최종 패키지로 합침.
    "review",  # Review agent. 산출물 간 불일치, 참조 오류, 품질 문제를 검사.
]

# 전체 workflow의 현재 상태.
WorkflowStatus = Literal[
    "idle",  # 아직 실행 전.
    "running",  # 어떤 agent가 실행 중.
    "wait_user",  # 사용자 추가 답변이 필요한 상태.
    "needs_revision",  # Review 결과 수정이 필요한 상태.
    "completed",  # 전체 작업 완료.
    "failed",  # 에러로 중단.
]

# 위험도/심각도 공통 표현.
RiskLevel = Literal["low", "medium", "high", "unknown"]

# 청구항 종류: 독립항인지 종속항인지.
ClaimType = Literal["independent", "dependent"]

# 청구항 카테고리: 방법항, 시스템항, 장치항, 기록매체항 등.
ClaimCategory = Literal[
    "method",  # ~하는 방법.
    "system",  # ~하는 시스템.
    "device",  # ~하는 장치.
    "apparatus",  # 장치/기구 계열 표현. device와 유사하나 문서에 따라 구분 가능.
    "storage_medium",  # 컴퓨터 판독가능 기록매체.
    "program",  # 프로그램 청구항.
    "training_method",  # AI 모델 학습 방법.
    "inference_method",  # AI 모델 추론/판단 방법.
    "unknown",  # 아직 분류되지 않음.
]

# 도면 종류: 시스템 구성도, 흐름도, 데이터 흐름도 등.
FigureType = Literal[
    "system_architecture",  # 시스템/장치 구성도.
    "flowchart",  # 방법 단계 흐름도.
    "data_flow",  # 입력-처리-출력 데이터 흐름도.
    "model_structure",  # AI 모델 구조도.
    "ui",  # 화면/UI 예시도.
    "hardware_structure",  # 하드웨어 구조도.
    "sequence",  # 메시지/프로토콜 순서도.
    "other",  # 기타 도면.
]


# -----------------------------------------------------------------------------
# 2. Workflow / 실행 추적 State
# -----------------------------------------------------------------------------

class TraceEvent(TypedDict, total=False):
    """각 노드/agent가 무엇을 했는지 남기는 짧은 로그. 숨은 CoT는 저장하지 않는다."""

    agent: AgentName  # 실행한 agent 이름.
    node: str  # LangGraph 내부 노드 이름. 예: slot_extract, route_next.
    action: str  # 수행한 작업. 예: extract_slots, generate_claims.
    summary: str  # 사람이 볼 수 있는 짧은 요약.
    timestamp: str  # 실행 시각 문자열.
    inputs: dict[str, Any]  # 디버깅용 입력 요약. 민감정보/긴 전문은 피한다.
    outputs: dict[str, Any]  # 디버깅용 출력 요약. 전체 문서 전문 저장은 피한다.


class WorkflowState(TypedDict, total=False):
    """현재 workflow가 어디까지 진행됐는지 관리한다."""

    status: WorkflowStatus  # idle/running/wait_user/completed 등 전체 상태.
    current_agent: AgentName  # 지금 실행 중인 agent.
    next_agent: AgentName  # 다음에 실행할 agent.
    route_reason: str  # 왜 그 agent로 이동하는지 설명.
    iteration_count: int  # 반복 횟수. 무한 루프 방지용.
    max_iterations: int  # 최대 반복 횟수.
    trace: list[TraceEvent]  # 실행 로그 목록.
    errors: list[str]  # 에러 메시지 목록.


# -----------------------------------------------------------------------------
# 3. 상담 agent State
# -----------------------------------------------------------------------------

class FollowupQuestion(TypedDict, total=False):
    """상담 agent가 사용자에게 물어볼 추가 질문."""

    target_slot: str  # 어떤 발명 정보 슬롯을 채우기 위한 질문인지. 예: differentiation.
    question: str  # 실제 질문 문장.
    why_needed: str  # 왜 이 정보가 필요한지.
    based_on: str  # 어떤 사용자 입력/상태를 근거로 질문했는지.
    expected_answer_type: str  # 기대 답변 형태. 예: 구성요소 설명, 효과 설명.


class Component(TypedDict, total=False):
    """발명을 이루는 구성요소 하나. 예: 데이터 수집부, AI 분석부."""

    id: str  # 내부 식별자. 예: C001.
    name: str  # 구성요소 이름.
    role: str  # 구성요소 역할.
    type: str  # component/module/step/model 등 자유 분류.
    mandatory: bool  # 발명 핵심 필수 구성인지 여부.
    aliases: list[str]  # 별칭. 예: 분석부, 상기 분석부.
    source_text: str  # 사용자 입력 또는 문서에서 근거가 된 원문.


class ProcessStep(TypedDict, total=False):
    """방법항/흐름도에 쓰일 수 있는 처리 단계 하나."""

    id: str  # 내부 식별자. 예: S001.
    order: int  # 단계 순서.
    name: str  # 단계 이름.
    actor: str  # 수행 주체. 예: AI 분석부.
    input: list[str]  # 입력 데이터.
    output: list[str]  # 출력 데이터.
    description: str  # 단계 설명.
    mandatory: bool  # 필수 단계인지 여부.


class ConsultationState(TypedDict, total=False):
    """상담 agent가 사용자 입력을 발명 정보로 구조화한 결과."""

    user_input: str  # 사용자의 원래 발명 설명.
    invention_title: str  # 발명 명칭 후보.
    problem: str  # 해결하려는 문제.
    background: str  # 배경 상황/기존 문제.
    solution: str  # 해결 수단.
    components: list[Component]  # 구성요소 목록.
    process_steps: list[ProcessStep]  # 처리 단계 목록.
    input_data: list[str]  # 입력 데이터.
    output_result: str  # 출력 결과.
    ai_usage: str  # AI가 실제로 하는 역할.
    application_domain: str  # 적용 분야. 예: 제조, 의료, 교육.
    effect: str  # 기술적 효과.
    differentiation: str  # 기존기술 대비 차이점.
    claim_like_features: list[str]  # 청구항에 들어갈 만한 핵심 특징.
    missing_slots: list[str]  # 아직 부족한 정보 필드.
    followup_questions: list[FollowupQuestion]  # 추가 질문 목록.
    completeness_score: float  # 발명 정보 완성도 점수.


# -----------------------------------------------------------------------------
# 4. 선행기술조사 agent State
# -----------------------------------------------------------------------------

class PriorArtCandidate(TypedDict, total=False):
    """검색된 선행문헌/특허 후보 하나."""

    patent_id: str  # 내부 특허 ID.
    title: str  # 특허 제목.
    publication_no: str  # 공개번호/등록번호.
    ipc_codes: list[str]  # IPC/CPC 코드.
    score: float  # 검색 점수. 법적 확신도가 아님.
    score_note: str  # 점수 의미 설명.
    overlap_points: list[str]  # 우리 발명과 겹치는 점.
    difference_points: list[str]  # 차이점.
    evidence: list[dict[str, Any]]  # 근거 문장/청구항/요약 조각.
    pdf_path: str  # 원문 PDF 경로.
    url: str  # 외부 링크가 있으면 저장.


class PriorArtState(TypedDict, total=False):
    """선행기술 검색/분석 결과."""

    search_query: str  # 검색에 사용한 대표 쿼리.
    expanded_queries: list[str]  # 확장 검색어.
    ipc_focus: list[str]  # 집중 IPC. 예: G06F, G06N, G06V.
    search_focus: list[str]  # problem/solution/components 등 검색 초점.
    candidates: list[PriorArtCandidate]  # 검색 후보 목록.
    closest_candidate_ids: list[str]  # 가장 가까운 후보 ID들.
    overlap_points: list[str]  # 전체적으로 겹치는 핵심 포인트.
    difference_points: list[str]  # 전체적으로 다른 핵심 포인트.
    novelty_risk: RiskLevel  # 신규성 리스크.
    inventive_step_risk: RiskLevel  # 진보성 리스크.
    analysis_summary: str  # 분석 요약.
    limitations: list[str]  # 한계/불확실성.


# -----------------------------------------------------------------------------
# 5. 청구항 생성 agent State
# -----------------------------------------------------------------------------

class ClaimDraft(TypedDict, total=False):
    """생성된 청구항 하나."""

    claim_no: int  # 청구항 번호.
    type: ClaimType  # independent/dependent.
    category: ClaimCategory  # method/system/storage_medium 등.
    depends_on: list[int]  # 종속항이면 참조하는 부모 청구항 번호.
    elements: list[str]  # 청구항 구성요소/단계 목록.
    text: str  # 실제 청구항 문장.
    source_components: list[str]  # 어떤 발명 구성요소에서 왔는지.
    review_flags: list[str]  # 검토 필요 표시.


class ClaimState(TypedDict, total=False):
    """청구항 설계도와 생성 결과."""

    claim_plan: dict[str, Any]  # 청구항 작성 전 설계도. claim 1 핵심, family 계획 등.
    draft_claims: list[ClaimDraft]  # 실제 생성된 청구항 목록.
    claim_dependency_graph: dict[str, Any]  # 제1항/제2항 의존관계 그래프.
    independent_claim_numbers: list[int]  # 독립항 번호 목록.
    dependent_claim_numbers: list[int]  # 종속항 번호 목록.
    claim_strategy_notes: list[str]  # 권리범위/작성 전략 메모.


# -----------------------------------------------------------------------------
# 6. 도면 agent State
# -----------------------------------------------------------------------------

class FigureSpec(TypedDict, total=False):
    """도면 하나에 대한 설계 정보."""

    fig_no: int  # 도면 번호. 예: 1이면 도 1.
    title: str  # 도면 제목.
    type: FigureType  # 도면 종류.
    purpose: str  # 이 도면이 설명하려는 목적.
    components: list[str]  # 도면에 들어가는 구성요소.
    steps: list[str]  # 흐름도라면 들어가는 단계.
    description: str  # 도면 설명 초안.


class ReferenceNumeral(TypedDict, total=False):
    """도면 참조부호 하나. 예: 110 = 데이터 수집부."""

    number: str  # 참조부호 번호.
    term: str  # 해당 구성요소 이름.
    figure: str  # 등장 도면. 예: 도 1.
    component_id: str  # Component.id와 연결.
    description: str  # 짧은 설명.


class DrawingState(TypedDict, total=False):
    """도면 구성과 참조부호 계획."""

    figures: list[FigureSpec]  # 도면 목록.
    reference_numerals: dict[str, ReferenceNumeral]  # 참조부호 map. key 예: "110".
    drawing_notes: list[str]  # 도면 작성/검토 메모.


# -----------------------------------------------------------------------------
# 7. 발명의 설명 agent State
# -----------------------------------------------------------------------------

class SpecificationState(TypedDict, total=False):
    """명세서 본문 섹션 초안."""

    technical_field: str  # 기술분야.
    background_art: str  # 배경기술.
    problem_to_solve: str  # 해결하려는 과제.
    means_for_solving: str  # 과제의 해결 수단.
    effects: str  # 발명의 효과.
    brief_description_of_drawings: str  # 도면의 간단한 설명.
    detailed_description: str  # 발명을 실시하기 위한 구체적인 내용.
    embodiment_notes: list[str]  # 실시예 관련 메모.


# -----------------------------------------------------------------------------
# 8. document_links: 문서 내부 참조/연결 State
# -----------------------------------------------------------------------------

class TermEntry(TypedDict, total=False):
    """용어 사전 항목. 같은 대상을 여러 표현으로 부를 때 기준점이 된다."""

    canonical_name: str  # 표준 명칭. 예: AI 분석부.
    type: str  # component/step/data/effect 등.
    aliases: list[str]  # 별칭. 예: 분석부, 상기 분석부.
    reference_no: str  # 참조부호. 예: 120.
    first_defined_in: str  # 처음 정의된 위치. 예: drawings.figures[0].
    used_in: list[str]  # 사용된 위치 목록.
    source_component_id: str  # 상담 state의 Component.id와 연결.


class LinkEntry(TypedDict, total=False):
    """두 대상 사이의 연결 관계. claim→component, figure→component 등에 공통 사용."""

    source: str  # 출발점. 예: claims.draft_claims[0].
    target: str  # 도착점. 예: consultation.components.C001.
    relation: str  # 관계 유형. 예: mentions, supports, refers_to.
    evidence: str  # 이 연결의 근거 문장/필드.
    confidence: float  # 연결 신뢰도.
    review_flag: str  # 불확실하거나 검토 필요한 내용.


class ParagraphAnchor(TypedDict, total=False):
    """명세서 문단 기준점. '상기' 같은 표현이 무엇을 가리키는지 추적하는 데 사용."""

    anchor_id: str  # 문단/대상 식별자. 예: P003.
    section: str  # 섹션명. 예: detailed_description.
    paragraph_id: str  # 문단 ID.
    entity: str  # 이 문단이 설명하는 대상. 예: AI 분석부.
    text: str  # 문단 원문 또는 요약.


class DocumentLinksState(TypedDict, total=False):
    """문서 내부 참조 관계를 저장한다.

    해결하려는 문제:
    - "상기 분석부"가 무엇을 가리키는지
    - "도 1"과 참조부호 "120"이 어떤 구성요소와 연결되는지
    - 청구항 구성요소가 도면/명세서에서 뒷받침되는지
    - 제1항/제2항 참조 관계가 꼬이지 않았는지
    """

    term_registry: dict[str, TermEntry]  # 용어 사전.
    reference_numeral_map: dict[str, ReferenceNumeral]  # 참조부호 map.
    claim_to_component_links: list[LinkEntry]  # 청구항과 구성요소 연결.
    figure_to_component_links: list[LinkEntry]  # 도면과 구성요소 연결.
    spec_support_links: list[LinkEntry]  # 명세서 문단이 청구항을 뒷받침하는 연결.
    anaphora_links: list[LinkEntry]  # 상기/전술한/이러한 표현 해소 연결.
    paragraph_anchors: list[ParagraphAnchor]  # 명세서 문단 기준점 목록.


# -----------------------------------------------------------------------------
# 9. invention_graph: 발명 구조/관계 State
# -----------------------------------------------------------------------------

class RelationEdge(TypedDict, total=False):
    """발명 구성요소 사이의 관계 하나. 예: 데이터 수집부 → AI 분석부."""

    source: str  # 관계 시작 구성요소/단계.
    target: str  # 관계 도착 구성요소/단계.
    relation: str  # 관계 유형. 예: provides_input_to, generates_result_for.
    direction: str  # 방향성 설명. 예: source_to_target.
    evidence: str  # 관계를 판단한 근거.
    confidence: float  # 신뢰도.
    mandatory: bool  # 발명 핵심 필수 관계인지.
    review_flag: str  # 검토 필요 표시.


class InventionGraphState(TypedDict, total=False):
    """발명의 구조 그래프. ReAct의 숨은 추론이 아니라 공유용 구조화 JSON이다."""

    component_graph: dict[str, Any]  # 구성요소 노드/관계 전체 구조.
    relation_edges: list[RelationEdge]  # 구성요소 간 관계 목록.
    data_flow_graph: dict[str, Any]  # 입력→처리→출력 흐름.
    mandatory_optional_judgement: dict[str, str]  # 필수/선택 판단. 예: C001=mandatory.
    claim_1_core_candidates: list[str]  # 청구항 1에 들어갈 핵심 후보.
    dependent_claim_candidates: list[str]  # 종속항으로 뺄 세부 후보.


# -----------------------------------------------------------------------------
# 10. drafting_options: 이번 실행의 작성 옵션
# -----------------------------------------------------------------------------

class DraftingOptionsState(TypedDict, total=False):
    """이번 실행에서 선택한 작성 옵션. 고정 규칙은 rules/*.yaml에 둔다."""

    claim_style: str  # 청구항 문체. 예: korean_patent.
    specification_tone: str  # 명세서 문체. 예: formal.
    use_reference_numerals: bool  # 참조부호를 사용할지.
    use_semicolon: bool  # 청구항 구성요소 사이 세미콜론을 사용할지.
    use_anaphora_phrases: bool  # 상기/전술한 표현을 사용할지.
    target_claim_categories: list[ClaimCategory]  # 생성 목표 청구항 카테고리.


# -----------------------------------------------------------------------------
# 11. Review agent State
# -----------------------------------------------------------------------------

class ReviewIssue(TypedDict, total=False):
    """Review agent가 발견한 문제 하나."""

    severity: RiskLevel  # 문제 심각도.
    target_agent: AgentName  # 피드백 받을 agent.
    target_path: str  # state 내부 위치. 예: claims.draft_claims[0].text.
    issue: str  # 문제 설명.
    suggestion: str  # 수정 제안.
    evidence: str  # 문제 판단 근거.


class ReviewState(TypedDict, total=False):
    """전체 산출물 검토 결과."""

    review_results: list[ReviewIssue]  # 발견된 문제 목록.
    overall_risk: RiskLevel  # 전체 위험도.
    feedback_to_agents: dict[str, list[str]]  # agent별 피드백 모음.
    consistency_score: float  # 청구항/도면/명세서 일관성 점수.
    passed: bool  # 통과 여부.


# -----------------------------------------------------------------------------
# 12. 최종 패키지 State
# -----------------------------------------------------------------------------

class FinalPackageState(TypedDict, total=False):
    """최종 명세서/보고서 산출물."""

    title: str  # 최종 발명 명칭.
    abstract: str  # 요약.
    claims: list[ClaimDraft]  # 최종 청구항.
    drawings: DrawingState  # 최종 도면 계획.
    specification: SpecificationState  # 최종 발명의 설명.
    prior_art_report: PriorArtState  # 선행기술 보고서.
    review_report: ReviewState  # 리뷰 보고서.
    rendered_markdown: str  # 렌더링된 Markdown.
    rendered_html_path: str  # HTML 파일 경로.
    rendered_docx_path: str  # DOCX 파일 경로.


# -----------------------------------------------------------------------------
# 13. 최상위 LangGraph 공유 State
# -----------------------------------------------------------------------------

class PatentAgentState(TypedDict, total=False):
    """LangGraph 전체에서 공유되는 최상위 State."""

    workflow: WorkflowState  # 현재 진행 상태/다음 agent/trace/error.
    messages: list[dict[str, Any]]  # 대화 메시지 기록. LangGraph messages와 연결 가능.

    consultation: ConsultationState  # 상담 agent 산출물.
    prior_art: PriorArtState  # 선행기술조사 agent 산출물.
    claims: ClaimState  # 청구항 agent 산출물.
    drawings: DrawingState  # 도면 agent 산출물.
    specification: SpecificationState  # 발명의 설명 agent 산출물.

    document_links: DocumentLinksState  # 상기/도면번호/참조부호/청구항 연결 정보.
    invention_graph: InventionGraphState  # 발명 구성요소/관계/데이터흐름 정보.
    drafting_options: DraftingOptionsState  # 이번 실행의 문체/작성 옵션.

    review: ReviewState  # Review agent 산출물.
    final_package: FinalPackageState  # 최종 명세서/보고서 산출물.


# -----------------------------------------------------------------------------
# 14. 초기 State 생성 함수
# -----------------------------------------------------------------------------

def create_initial_state(user_input: str = "") -> PatentAgentState:
    """그래프 첫 실행 또는 테스트용 빈 State를 만든다."""

    return {
        "workflow": {
            "status": "idle",
            "current_agent": "master",
            "next_agent": "consultation",
            "iteration_count": 0,
            "max_iterations": 8,
            "trace": [],
            "errors": [],
        },
        "messages": [],
        "consultation": {
            "user_input": user_input,
            "components": [],
            "process_steps": [],
            "input_data": [],
            "claim_like_features": [],
            "missing_slots": [],
            "followup_questions": [],
        },
        "prior_art": {"candidates": [], "limitations": []},
        "claims": {"draft_claims": [], "claim_strategy_notes": []},
        "drawings": {"figures": [], "reference_numerals": {}, "drawing_notes": []},
        "specification": {"embodiment_notes": []},
        "document_links": {
            "term_registry": {},
            "reference_numeral_map": {},
            "claim_to_component_links": [],
            "figure_to_component_links": [],
            "spec_support_links": [],
            "anaphora_links": [],
            "paragraph_anchors": [],
        },
        "invention_graph": {
            "component_graph": {},
            "relation_edges": [],
            "data_flow_graph": {},
            "mandatory_optional_judgement": {},
            "claim_1_core_candidates": [],
            "dependent_claim_candidates": [],
        },
        "drafting_options": {
            "claim_style": "korean_patent",
            "specification_tone": "formal",
            "use_reference_numerals": True,
            "use_semicolon": True,
            "use_anaphora_phrases": True,
            "target_claim_categories": ["method", "system", "storage_medium"],
        },
        "review": {
            "review_results": [],
            "overall_risk": "unknown",
            "feedback_to_agents": {},
            "passed": False,
        },
        "final_package": {},
    }
