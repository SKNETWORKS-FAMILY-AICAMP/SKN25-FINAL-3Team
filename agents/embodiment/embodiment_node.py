"""LangGraph 노드 연결부. embodiment_agent.py의 기존 로직을 State 기반으로 감싼다.

입력:
    state["specification"] - 발명의 설명 에이전트 결과 (SpecificationState)
    state["claims"]        - 청구항 에이전트 결과 (ClaimState)
    state["drawings"]      - 도면 에이전트 결과 (DrawingState)

출력:
    state["specification"]["brief_description_of_drawings"] - 도면의 간단한 설명
    state["specification"]["embodiment_notes"]              - 도면별 실시예 목록
"""

from __future__ import annotations

import json

from agents.embodiment.embodiment_agent import generate_drawing_description_and_embodiments


def _spec_to_str(spec: dict) -> str:
    """SpecificationState → GPT에 넘길 문자열."""
    parts = []
    if spec.get("technical_field"):    parts.append(f"기술분야: {spec['technical_field']}")
    if spec.get("background_art"):     parts.append(f"배경기술: {spec['background_art']}")
    if spec.get("problem_to_solve"):   parts.append(f"해결과제: {spec['problem_to_solve']}")
    if spec.get("means_for_solving"):  parts.append(f"해결수단: {spec['means_for_solving']}")
    if spec.get("effects"):            parts.append(f"효과: {spec['effects']}")
    if spec.get("detailed_description"):
        parts.append(f"상세설명: {spec['detailed_description']}")
    return "\n".join(parts) if parts else "(발명의 설명 없음)"


def _claims_to_str(claims: dict) -> str:
    """ClaimState → GPT에 넘길 문자열."""
    drafts = claims.get("draft_claims", [])
    if not drafts:
        return "(청구항 없음)"
    lines = []
    for c in drafts:
        lines.append(f"제{c.get('claim_no', '?')}항 ({c.get('type', '')}): {c.get('text', '')}")
    return "\n".join(lines)


def _figures_from_state(drawings: dict) -> list:
    """DrawingState.figures(FigureSpec) → embodiment_agent이 받는 figures 형식.

    embodiment_agent는 fig_json의 elements/relations가 있으면 더 정확하지만,
    State에는 components/steps만 있으므로 이를 elements 형식으로 변환한다.
    """
    figures = []
    for fig in drawings.get("figures", []):
        elements = []
        # flowchart 계열은 steps → elements
        if fig.get("type") in ("flowchart",) and fig.get("steps"):
            for i, step in enumerate(fig["steps"]):
                elements.append({
                    "id": f"S{(i+1)*100}",
                    "ref_no": f"S{(i+1)*100}",
                    "name": step,
                    "shape_type": "process",
                })
        else:
            ref_map = drawings.get("reference_numerals", {})
            for i, comp_name in enumerate(fig.get("components", [])):
                ref_no = str(100 + i * 10)
                # reference_numerals에서 실제 번호 찾기
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


def embodiment_node(state: dict) -> dict:
    """LangGraph 노드 함수.

    도면의 간단한 설명 + 도면별 실시예를 생성해 state["specification"]에 추가한다.
    """
    drawings = state.get("drawings", {})
    if not drawings.get("figures"):
        workflow = state.get("workflow", {})
        return {
            "workflow": {
                **workflow,
                "errors": [*workflow.get("errors", []),
                           "embodiment_node: drawings.figures 없음 (도면 에이전트 먼저 실행 필요)"],
            }
        }

    spec   = state.get("specification", {})
    claims = state.get("claims", {})

    figures = _figures_from_state(drawings)

    result = generate_drawing_description_and_embodiments(
        invention_output=_spec_to_str(spec),
        claim_output=_claims_to_str(claims),
        figures=figures,
    )

    # brief_description_of_drawings: list → 하나의 문자열로 합치기
    brief_list = result.get("brief_description_of_drawings", [])
    brief_str = "\n".join(
        f"{item.get('fig_number', '')}: {item.get('description', '')}"
        for item in brief_list
    )

    # embodiments: list → list[str] (SpecificationState.embodiment_notes 형식)
    embodiment_notes = [
        f"{item.get('title', '')}\n{item.get('content', '')}"
        for item in result.get("embodiments", [])
    ]

    workflow = state.get("workflow", {})
    return {
        "specification": {
            **spec,
            "brief_description_of_drawings": brief_str,
            "embodiment_notes": embodiment_notes,
        },
        "workflow": {
            **workflow,
            "current_agent": "embodiment",
            "next_agent": "review",
        },
    }
