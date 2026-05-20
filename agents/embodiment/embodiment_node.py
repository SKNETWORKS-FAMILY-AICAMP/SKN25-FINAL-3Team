"""LangGraph 노드 연결부. embodiment_agent.py의 기존 로직을 State 기반으로 감싼다.

embodiment_agent.py는 건드리지 않는다.
이 파일만 LangGraph 그래프 조립 시 import한다.

입력:
    state["drawings"]      - 도면 에이전트 결과 (DrawingState)
    state["specification"] - 발명의 설명 에이전트 결과 (SpecificationState)
    state["claims"]        - 청구항 에이전트 결과 (ClaimState)

출력:
    state["specification"]["brief_description_of_drawings"] - 도면의 간단한 설명
    state["specification"]["embodiment_notes"]              - 도면별 실시예 목록
    state["workflow"]

사용 예:
    from agents.embodiment.embodiment_node import embodiment_node

    graph.add_node("embodiment", embodiment_node)
    graph.add_edge("drawing", "embodiment")
"""

from __future__ import annotations

from agents.embodiment.embodiment_agent import generate_drawing_description_and_embodiments


# 빈 specification 업데이트 — 에러 시 반환하는 안전한 기본값
_EMPTY_SPEC_UPDATE: dict = {
    "brief_description_of_drawings": "",
    "embodiment_notes": [],
}


# ── 입력 변환 ──────────────────────────────────────────────────────────

def _spec_to_str(spec: dict) -> str:
    """SpecificationState → GPT에 넘길 문자열. 비어있어도 안전하게 처리."""
    parts: list[str] = []
    if spec.get("technical_field"):      parts.append(f"기술분야: {spec['technical_field']}")
    if spec.get("background_art"):       parts.append(f"배경기술: {spec['background_art']}")
    if spec.get("problem_to_solve"):     parts.append(f"해결과제: {spec['problem_to_solve']}")
    if spec.get("means_for_solving"):    parts.append(f"해결수단: {spec['means_for_solving']}")
    if spec.get("effects"):              parts.append(f"효과: {spec['effects']}")
    if spec.get("detailed_description"): parts.append(f"상세설명: {spec['detailed_description']}")
    return "\n".join(parts) if parts else "(발명의 설명 없음)"


def _claims_to_str(claims: dict) -> str:
    """ClaimState → GPT에 넘길 문자열. 비어있어도 안전하게 처리."""
    drafts = (claims or {}).get("draft_claims") or []
    if not drafts:
        return "(청구항 없음)"
    return "\n".join(
        f"제{c.get('claim_no', '?')}항 ({c.get('type', '')}): {c.get('text', '')}"
        for c in drafts
    )


def _figures_from_drawing_state(drawings: dict) -> list:
    """DrawingState.figures → embodiment_agent이 받는 figures 형식.

    embodiment_agent는 fig_json의 elements/relations를 사용한다.
    DrawingState에는 components/steps만 있으므로 elements 형식으로 변환한다.
    """
    figures: list = []
    ref_map = (drawings or {}).get("reference_numerals") or {}

    for fig in (drawings or {}).get("figures") or []:
        elements: list = []

        if fig.get("type") == "flowchart" and fig.get("steps"):
            for i, step in enumerate(fig["steps"]):
                elements.append({
                    "id": f"S{(i + 1) * 100}",
                    "ref_no": f"S{(i + 1) * 100}",
                    "name": step,
                    "shape_type": "process",
                })
        else:
            for i, comp_name in enumerate(fig.get("components") or []):
                ref_no = str(100 + i * 10)
                for num, ref in ref_map.items():
                    if ref.get("term") == comp_name:
                        ref_no = num
                        break
                elements.append({
                    "id": f"N{ref_no}",
                    "ref_no": ref_no,
                    "name": comp_name,
                    "type": "module",
                })

        figures.append({
            "fig_number": f"도 {fig.get('fig_no', '?')}",
            "title": fig.get("title", ""),
            "diagram_type": fig.get("type", "system_architecture"),
            "fig_json": {
                "elements": elements,
                "relations": [],
                "title": fig.get("title", ""),
                "diagram_type": fig.get("type", "system_architecture"),
            },
        })

    return figures


# ── LangGraph 노드 ─────────────────────────────────────────────────────

def embodiment_node(state: dict) -> dict:
    """LangGraph 노드 함수.

    도면의 간단한 설명 + 도면별 실시예를 생성해 state["specification"]에 추가한다.

    어떤 state가 들어와도 예외를 바깥으로 던지지 않는다.
    실패 시 빈 값 + workflow.errors에 메시지를 기록한다.
    """
    workflow = state.get("workflow") or {}
    errors: list[str] = list(workflow.get("errors") or [])
    spec    = state.get("specification") or {}
    claims  = state.get("claims") or {}
    drawings = state.get("drawings") or {}

    figures = _figures_from_drawing_state(drawings)

    # figures가 없으면 LLM 호출 없이 빈 값으로 반환
    if not figures:
        errors.append("embodiment_node: drawings.figures 없음 (도면 에이전트 먼저 실행 필요)")
        return {
            "specification": {**spec, **_EMPTY_SPEC_UPDATE},
            "workflow": {
                **workflow,
                "errors": errors,
                "current_agent": "embodiment",
                "next_agent": "specification",
            },
        }

    result: dict = {}
    try:
        result = generate_drawing_description_and_embodiments(
            invention_output=_spec_to_str(spec),
            claim_output=_claims_to_str(claims),
            figures=figures,
        )
    except Exception as e:
        errors.append(f"embodiment_node: generate 실패 — {e}")

    # brief_description_of_drawings: list → 하나의 문자열
    brief_list = result.get("brief_description_of_drawings") or []
    brief_str = "\n".join(
        f"{item.get('fig_number', '')}: {item.get('description', '')}"
        for item in brief_list
    )

    # embodiments: list → list[str]
    embodiment_notes = [
        f"{item.get('title', '')}\n{item.get('content', '')}"
        for item in (result.get("embodiments") or [])
    ]

    return {
        "specification": {
            **spec,
            "brief_description_of_drawings": brief_str,
            "embodiment_notes": embodiment_notes,
        },
        "workflow": {
            **workflow,
            "errors": errors,
            "current_agent": "embodiment",
            "next_agent": "specification",
        },
    }
