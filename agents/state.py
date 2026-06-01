"""특허 agent 서비스의 공유 실행 state를 정의합니다.

중복 방지 원칙:
- 각 agent의 상세 output 계약은 `agents/schemas/*.py`의 Pydantic 모델이 단일 기준입니다.
- `PatentAgentState`는 LangGraph/FastAPI가 공유하는 컨테이너만 정의합니다.
- agent 결과는 adapter에서 Pydantic 검증 후 `model_dump()`된 dict로 저장합니다.

즉, state.py는 schema 필드를 다시 복붙하지 않고 실행 상태, 사용자 입력,
agent별 결과 저장 위치, artifact/session 메타데이터만 관리합니다.
"""
from __future__ import annotations

from typing import Any, Literal, TypedDict

# ──────────────────────────────────────────────
# 타입 별칭 (Literal)
# ──────────────────────────────────────────────
# Literal은 "이 변수는 이 값들 중 하나만 가능하다"를 타입으로 표현합니다.
# 예: AgentName = "summary" | "claim" | ... 처럼 허용된 agent 이름만 쓸 수 있게 제한합니다.

AgentName = Literal[
    "master",
    "summary",
    "prior_art",
    "claim",
    "drawing",
    "specification",
    "composer",
    "review",  # TODO: 미구현. adapter/agent/schema 작업 후 master/router.py SERVICE_PIPELINE에 추가 예정.
]

# 파이프라인 전체의 진행 상태를 나타내는 값 목록입니다.
# "idle"=시작 전, "running"=실행 중, "wait_user"=사용자 입력 대기,
# "needs_revision"=수정 필요, "completed"=완료, "failed"=실패
WorkflowStatus = Literal[
    "idle",
    "running",
    "wait_user",
    "needs_revision",
    "completed",
    "failed",
]


# ──────────────────────────────────────────────
# TypedDict란?
# ──────────────────────────────────────────────
# TypedDict는 Python dict에 키와 값의 타입을 명시하는 방법입니다.
# 일반 dict는 어떤 키/값이든 넣을 수 있지만,
# TypedDict를 쓰면 IDE와 타입 검사기가 잘못된 키나 타입을 잡아줍니다.
# total=False는 "모든 키가 필수는 아니다(선택적이다)"는 뜻입니다.

class TraceEvent(TypedDict, total=False):
    """agent 실행 이력을 남기는 짧은 로그입니다.

    파이프라인이 실행되는 동안 각 단계에서 무슨 일이 있었는지 기록합니다.
    디버깅이나 사용자에게 진행 상황을 보여줄 때 씁니다.
    """

    agent: str       # 어떤 agent가 실행됐는지 (예: "summary", "claim")
    node: str        # LangGraph 노드 이름 (추후 LangGraph 전환 시 사용)
    action: str      # 무슨 동작을 했는지 (예: "run", "skip", "retry")
    summary: str     # 한 줄 요약
    timestamp: str   # 실행 시각 (ISO 8601 문자열)
    inputs: dict[str, Any]   # agent에 넘긴 입력 (디버깅용)
    outputs: dict[str, Any]  # agent가 반환한 출력 (디버깅용)


class WorkflowState(TypedDict, total=False):
    """현재 workflow 진행 상태와 에러/추적 정보를 관리합니다.

    graph.py가 파이프라인을 실행하면서 이 dict를 직접 수정합니다.
    프론트엔드는 이 값을 보고 "지금 어느 단계인지" 사용자에게 보여줄 수 있습니다.
    """

    status: WorkflowStatus     # 파이프라인 전체 상태 (위 WorkflowStatus 참고)
    current_agent: str         # 지금 실행 중인 agent 이름
    next_agent: str            # 다음에 실행할 agent 이름
    route_reason: str          # master router가 이 순서를 선택한 이유
    iteration_count: int       # 현재까지 실행한 agent 수
    max_iterations: int        # 무한 루프 방지를 위한 최대 실행 횟수
    trace: list[TraceEvent]    # 지금까지의 실행 이력 목록
    errors: list[str]          # 실행 중 발생한 에러 메시지 목록


class PatentAgentState(TypedDict, total=False):
    """서비스 graph 전체에서 공유하는 최상위 state 컨테이너입니다.

    ─ 이 dict 하나가 파이프라인을 흐르는 "공유 작업판"입니다 ─

    모든 agent는 이 state를 읽고(input), 자신의 결과를 이 state에 씁니다(output).
    FastAPI API 응답에도 이 state가 그대로 담겨 프론트엔드로 전달됩니다.

    각 agent output의 내부 필드 구조는 이 파일이 아니라
    `agents/schemas/*.py`의 Pydantic schema가 책임집니다.
    """

    # ── 파이프라인 인프라 필드 ──────────────────────────
    # graph.py, pipeline.py가 직접 관리합니다.

    workflow: WorkflowState       # 파이프라인 실행 상태 (running/completed 등)
    run_session: dict[str, Any]   # run_id 등 이번 실행 세션 메타데이터. DB 연결 전까지 임시.
    user_input: str               # 사용자가 입력한 발명 설명 원문
    messages: list[dict[str, Any]] # 대화 이력 (추후 멀티턴 대화 지원 시 사용 예정)

    # ── agent별 결과 저장 공간 ──────────────────────────
    # 각 agent의 adapter가 실행 완료 후 여기에 결과를 저장합니다.
    # 내부 구조는 agents/schemas/*.py의 Pydantic 모델을 참고하세요.

    summary: dict[str, Any]        # SummaryAgent 결과 → agents/schemas/summary.py
    prior_art: dict[str, Any]      # PriorArtAgent 결과 → agents/schemas/prior_art.py
    claims: dict[str, Any]         # ClaimAgent 결과 → agents/schemas/claim.py
    drawings: dict[str, Any]       # DrawingAgent 결과 → agents/schemas/drawing.py
    specification: dict[str, Any]  # SpecificationAgent 결과 → agents/schemas/specification.py
    composer: dict[str, Any]       # ComposerAgent 중간 데이터 (현재 미사용)
    review: dict[str, Any]         # TODO: 미구현. 저장 위치 예약만 해둠.
    final_package: dict[str, Any]  # ComposerAgent 최종 출력 (렌더링된 문서 패키지)

    # ── 라우팅/판단 결과 ──────────────────────────
    master_decision: dict[str, Any]  # MasterDecision 모델의 model_dump() 결과.
                                     # "다음 agent가 뭔지", "사용자 입력이 더 필요한지" 등 포함.

    # ── 문서 연결 정보 (DocumentLinks) ──────────────────
    # 청구항·도면·명세서 간의 용어/번호/단락 연결 정보입니다.
    # create_initial_state()에서 초기 구조만 잡혀 있고, 아직 agent가 채우지 않습니다.
    document_links: dict[str, Any]

    # ── 발명 구조 그래프 (InventionGraph) ──────────────
    # 발명의 구성요소와 관계를 그래프로 표현하는 공간입니다.
    # 청구항·도면 agent가 구성요소 관계를 분석할 때 쓸 예정입니다. (미구현)
    invention_graph: dict[str, Any]

    # ── 작성 옵션 (DraftingOptions) ──────────────────
    # "청구항 스타일", "명세서 어조" 같은 문서 작성 설정값입니다.
    # create_initial_state()에서 기본값이 채워집니다. 사용자가 변경 가능하도록 설계 예정.
    drafting_options: dict[str, Any]

    # ── 생성된 파일 목록 (Artifacts) ──────────────────
    # 파이프라인이 만든 PDF·DOCX·HTML·SVG 파일의 경로/URL을 저장합니다.
    # DB와 파일 스토리지가 연결되면 여기에 artifact 메타데이터가 쌓입니다. (미구현)
    artifacts: dict[str, Any]


def create_initial_state(user_input: str = "") -> PatentAgentState:
    """새 실행 또는 테스트용 빈 state를 만듭니다.

    파이프라인을 처음 시작할 때 이 함수를 호출해서 빈 state를 만든 뒤,
    각 agent가 순서대로 자신의 결과를 채워 넣습니다.
    """

    return {
        # 파이프라인 실행 상태 초기값
        "workflow": {
            "status": "idle",           # 아직 시작 전
            "current_agent": "master",  # master router가 첫 번째로 판단
            "next_agent": "summary",    # 첫 번째로 실행할 agent
            "iteration_count": 0,
            "max_iterations": 8,        # 8단계 이상 실행되면 무한 루프로 간주
            "trace": [],
            "errors": [],
        },
        "run_session": {},   # pipeline.py에서 run_id 등을 넣어줌
        "user_input": user_input,
        "messages": [],

        # agent 결과 공간 (모두 빈 dict로 시작)
        "summary": {},
        "prior_art": {},
        "claims": {},
        "drawings": {},
        "specification": {},
        "composer": {},
        "review": {},
        "final_package": {},

        # document_links: 청구항·도면·명세서 간 용어/번호 연결 정보의 초기 구조
        "document_links": {
            "term_registry": {},           # 용어 사전 (용어 → 정의/동의어)
            "reference_numeral_map": {},   # 참조 번호 지도 (번호 → 구성요소 이름)
            "claim_to_component_links": [], # 청구항 구성요소 ↔ 도면 구성요소 연결
            "figure_to_component_links": [], # 도면 번호 ↔ 구성요소 연결
            "spec_support_links": [],       # 명세서 단락 ↔ 청구항 지지 연결
            "anaphora_links": [],           # "상기 ~" 같은 지시어 해소 연결
            "paragraph_anchors": [],        # 명세서 단락 앵커 (문단 번호 등)
        },

        # invention_graph: 발명 구성요소 관계 그래프의 초기 구조
        "invention_graph": {
            "component_graph": {},              # 구성요소 간 관계 (노드·엣지)
            "relation_edges": [],               # 관계 엣지 목록
            "data_flow_graph": {},              # 데이터 흐름 그래프
            "mandatory_optional_judgement": {}, # 각 구성요소의 필수/선택 여부
            "claim_1_core_candidates": [],      # 독립 청구항 1항 핵심 후보
            "dependent_claim_candidates": [],   # 종속항 후보
        },

        # drafting_options: 문서 작성 스타일 기본값
        "drafting_options": {
            "claim_style": "korean_patent",          # 한국 특허 청구항 스타일
            "specification_tone": "formal",           # 명세서 문체 (격식체)
            "use_reference_numerals": True,           # 참조 번호 사용 여부
            "use_semicolon": True,                    # 청구항 세미콜론 구분 사용
            "use_anaphora_phrases": True,             # "상기" 같은 지시어 사용
            "target_claim_categories": ["method", "system", "storage_medium"],
            # ^ 방법/시스템/저장매체 3종 세트로 청구항 작성
        },

        "master_decision": {},
        "artifacts": {},
    }
