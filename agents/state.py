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

AgentName = Literal[
    "master",
    "summary",
    "prior_art",
    "claim",
    "drawing",
    "specification",
    "composer",
    "review",
]

WorkflowStatus = Literal[
    "idle",
    "running",
    "wait_user",
    "needs_revision",
    "completed",
    "failed",
]


class TraceEvent(TypedDict, total=False):
    """agent 실행 이력을 남기는 짧은 로그입니다. 숨은 추론 전문은 저장하지 않습니다."""

    agent: str
    node: str
    action: str
    summary: str
    timestamp: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]


class WorkflowState(TypedDict, total=False):
    """현재 workflow 진행 상태와 에러/추적 정보를 관리합니다."""

    status: WorkflowStatus
    current_agent: str
    next_agent: str
    route_reason: str
    iteration_count: int
    max_iterations: int
    trace: list[TraceEvent]
    errors: list[str]


class PatentAgentState(TypedDict, total=False):
    """서비스 graph 전체에서 공유하는 최상위 state 컨테이너입니다.

    `summary`, `prior_art`, `claims`, `drawings`, `specification`, `composer`,
    `review`, `final_package`의 내부 필드 구조는 이 파일이 아니라
    `agents/schemas/*.py`의 Pydantic output schema가 책임집니다.
    """

    workflow: WorkflowState
    run_session: dict[str, Any]
    user_input: str
    messages: list[dict[str, Any]]

    summary: dict[str, Any]
    prior_art: dict[str, Any]
    claims: dict[str, Any]
    drawings: dict[str, Any]
    specification: dict[str, Any]
    composer: dict[str, Any]
    review: dict[str, Any]
    final_package: dict[str, Any]

    document_links: dict[str, Any]
    invention_graph: dict[str, Any]
    drafting_options: dict[str, Any]
    master_decision: dict[str, Any]
    artifacts: dict[str, Any]


def create_initial_state(user_input: str = "") -> PatentAgentState:
    """새 실행 또는 테스트용 빈 state를 만듭니다."""

    return {
        "workflow": {
            "status": "idle",
            "current_agent": "master",
            "next_agent": "summary",
            "iteration_count": 0,
            "max_iterations": 8,
            "trace": [],
            "errors": [],
        },
        "run_session": {},
        "user_input": user_input,
        "messages": [],
        "summary": {},
        "prior_art": {},
        "claims": {},
        "drawings": {},
        "specification": {},
        "composer": {},
        "review": {},
        "final_package": {},
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
        "master_decision": {},
        "artifacts": {},
    }
