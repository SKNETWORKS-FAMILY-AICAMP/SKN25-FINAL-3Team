from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class PatentAgentState(TypedDict):
    # 사용자 입력
    user_input: str
    user_id: str
    session_id: str

    # Consulting Agent 출력
    is_consultation_done: bool      # True이면 Phase 2(명세서 생성)로 전환
    next_question: str              # UI에 표시할 AI 응답/질문
    invention_flow: str
    problem: str
    differentiation: str
    effect: str
    raw_conversation: Annotated[list, add_messages]

    # Patent Search Agent 출력
    similar_patents: list       # [{id, title, similarity, summary_problem, summary_solution}]
    ipc_codes: list

    # Claims Agent 출력
    claims: list                # [{"claim_number", "claim_type", "is_independent", "depends_on", "content"}]

    # Examiner Agent 출력
    is_registerable: Optional[bool]
    examiner_opinion: str
    examiner_issues: list       # [{"claim_number", "reason"}]
    revision_count: int         # 청구항 재작성 횟수 (graph.py MAX_REVISION 참고)

    # Drawing Agent 출력
    flowchart_code: str
    system_diagram_code: str

    # Description Agent 출력
    background: str
    problem_statement: str
    solution: str
    drawing_description: str
    detailed_description: str
