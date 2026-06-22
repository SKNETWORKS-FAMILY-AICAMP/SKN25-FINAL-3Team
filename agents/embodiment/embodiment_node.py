"""LangGraph 노드 연결부. embodiment_agent.py의 기존 로직을 State 기반으로 감싼다.

embodiment_agent.py는 건드리지 않는다.
이 파일만 LangGraph 그래프 조립 시 import한다.

입력:
    state["drawings"]      - 도면 에이전트 결과 (DrawingAgentOutput.model_dump())
    state["specification"] - 발명의 설명 에이전트 결과 (SpecificationAgentOutput.model_dump())
    state["claims"]        - 청구항 에이전트 결과

출력 schema: agents/schemas/specification.py SpecificationAgentOutput
저장 위치  : state["specification"] (기존 값 위에 merge)

사용 예:
    from agents.embodiment.embodiment_node import embodiment_node

    graph.add_node("embodiment", embodiment_node)
    graph.add_edge("drawing", "embodiment")
"""

from __future__ import annotations

from agents.embodiment.embodiment_agent import generate_drawing_description_and_embodiments
from agents.schemas.specification import SpecificationAgentOutput
from agents.validation import safe_validate_output


# hard fallback
_FALLBACK = SpecificationAgentOutput(
    status="failed",
    summary="embodiment 생성 실패 — hard fallback",
    brief_description_of_drawings="",
)


# ── 입력 변환 ──────────────────────────────────────────────────────────

def _spec_to_str(spec: dict) -> str:
    """SpecificationAgentOutput dict → GPT 프롬프트 문자열."""
    parts: list[str] = []
    if spec.get("technical_field"):      parts.append(f"기술분야: {spec['technical_field']}")
    if spec.get("background_art"):       parts.append(f"배경기술: {spec['background_art']}")
    if spec.get("problem_to_solve"):     parts.append(f"해결과제: {spec['problem_to_solve']}")
    if spec.get("means_for_solving"):    parts.append(f"해결수단: {spec['means_for_solving']}")
    if spec.get("effects"):              parts.append(f"효과: {spec['effects']}")
    if spec.get("detailed_description"): parts.append(f"상세설명: {spec['detailed_description']}")
    return "\n".join(parts) if parts else "(발명의 설명 없음)"


def _claims_to_str(claims: dict) -> str:
    """ClaimAgentOutput dict → GPT 프롬프트 문자열."""
    drafts = (claims or {}).get("draft_claims") or []
    if not drafts:
        return "(청구항 없음)"
    return "\n".join(
        f"제{c.get('claim_no', '?')}항 ({c.get('type', '')}): {c.get('text', '')}"
        for c in drafts
    )


def _figures_from_drawing_state(drawings: dict) -> list:
    """DrawingAgentOutput dict → embodiment_agent figures 형식.

    DrawingAgentOutput.reference_numerals는 list[ReferenceNumeral] (number/label/description).
    """
    figures: list = []
    # reference_numerals: list[dict] with number/label
    ref_list = (drawings or {}).get("reference_numerals") or []
    ref_map  = {r["number"]: r.get("label", "") for r in ref_list if isinstance(r, dict)}

    for fig in (drawings or {}).get("figures") or []:
        elements: list = []

        if fig.get("type") == "flowchart" and fig.get("components"):
            for i, name in enumerate(fig["components"]):
                elements.append({
                    "id": f"S{(i + 1) * 100}",
                    "ref_no": f"S{(i + 1) * 100}",
                    "name": name,
                    "shape_type": "process",
                })
        else:
            for i, comp_name in enumerate(fig.get("components") or []):
                ref_no = str(100 + i * 10)
                for num, label in ref_map.items():
                    if label == comp_name:
                        ref_no = num
                        break
                elements.append({
                    "id": f"N{ref_no}",
                    "ref_no": ref_no,
                    "name": comp_name,
                    "type": "module",
                })

        figures.append({
            "fig_number":  f"도 {fig.get('fig_no', '?')}",
            "title":       fig.get("title", ""),
            "diagram_type": fig.get("type", "system_architecture"),
            "fig_json": {
                "elements":    elements,
                "relations":   [],
                "title":       fig.get("title", ""),
                "diagram_type": fig.get("type", "system_architecture"),
            },
        })

    return figures


# ── LangGraph 노드 ─────────────────────────────────────────────────────

def embodiment_node(state: dict) -> dict:
    """LangGraph 노드 함수.

    도면의 간단한 설명 + 도면별 실시예를 생성해 state["specification"]에 merge한다.
    어떤 state가 들어와도 예외를 바깥으로 던지지 않는다.
    """
    workflow = state.get("workflow") or {}
    errors: list[str] = list(workflow.get("errors") or [])
    spec    = state.get("specification") or {}
    claims  = state.get("claims") or {}
    drawings = state.get("drawings") or {}

    figures = _figures_from_drawing_state(drawings)

    if not figures:
        errors.append("embodiment_node: drawings.figures 없음")
        fallback = _FALLBACK.model_copy()
        fallback.warnings.append("drawings.figures 없음 — 도면 에이전트 먼저 실행 필요")
        # 기존 spec 위에 fallback merge
        merged = {**spec, **fallback.model_dump()}
        return {
            "specification": merged,
            "workflow": {**workflow, "errors": errors,
                         "current_agent": "embodiment", "next_agent": "specification"},
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

    # brief_description_of_drawings
    brief_list = result.get("brief_description_of_drawings") or []
    brief_str = "\n".join(
        f"{item.get('fig_number', '')}: {item.get('description', '')}"
        for item in brief_list
    )

    # embodiment_notes → AgentOutputBase.notes 필드에 저장
    embodiment_notes = [
        f"{item.get('title', '')}\n{item.get('content', '')}"
        for item in (result.get("embodiments") or [])
    ]

    raw_output = {
        **spec,                                      # 기존 spec 필드 유지
        "status":                        "ok" if result else "failed",
        "summary":                       f"도면 {len(brief_list)}개 실시예 생성",
        "brief_description_of_drawings": brief_str,
        "notes":                         embodiment_notes,  # embodiment_notes → notes
    }

    validated = safe_validate_output(
        agent_name="embodiment",
        schema=SpecificationAgentOutput,
        raw_output=raw_output,
        fallback=_FALLBACK,
    )

    return {
        "specification": validated.model_dump(),
        "workflow": {
            **workflow,
            "errors":        errors,
            "current_agent": "embodiment",
            "next_agent":    "specification",
        },
    }
