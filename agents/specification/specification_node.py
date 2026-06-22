"""LangGraph 노드 연결부. specification_agent.py의 generate_specification을 State 기반으로 감싼다.

specification_agent.py는 건드리지 않는다.
이 파일만 LangGraph 그래프 조립 시 import한다.

출력 schema: agents/schemas/specification.py SpecificationAgentOutput
저장 위치  : state["specification"]

사용 예:
    from agents.specification.specification_node import specification_node

    graph.add_node("specification", specification_node)
    graph.add_edge("specification", "composer")
"""
from __future__ import annotations

from agents.schemas.specification import SpecificationAgentOutput
from agents.specification.specification_agent import generate_specification
from agents.validation import safe_validate_output

_FALLBACK = SpecificationAgentOutput(
    status="failed",
    summary="발명의 설명 생성 실패 — hard fallback",
)


# ── 입력 변환 ─────────────────────────────────────────────────────────

def _extract_invention_data(state: dict) -> dict:
    """PatentAgentState → generate_specification이 받는 data dict.

    summary.structured_invention 우선, 없으면 consultation 폴백.
    """
    summary_si = (state.get("summary") or {}).get("structured_invention") or {}
    consultation = state.get("consultation") or {}

    def _pick(*keys: str) -> str:
        for src in (summary_si, consultation):
            for k in keys:
                v = src.get(k)
                if v:
                    return str(v)
        return ""

    # 청구항
    claims_state = state.get("claims") or {}
    draft_claims = claims_state.get("draft_claims") or []
    independent = [c for c in draft_claims if c.get("type") == "independent"]
    dependent = [c for c in draft_claims if c.get("type") == "dependent"]

    claim_1_text = independent[0].get("text", "") if independent else ""
    dependent_texts = "\n".join(
        f"제{c.get('claim_no', i+2)}항: {c.get('text', '')}"
        for i, c in enumerate(dependent)
    )

    # 도면
    drawings_state = state.get("drawings") or {}
    figures = drawings_state.get("figures") or []
    drawing_list = [
        {
            "fig_number": f"도 {f.get('fig_no', i+1)}",
            "title": f.get("title", ""),
            "type": f.get("type", ""),
        }
        for i, f in enumerate(figures)
    ]

    # 알고리즘 단계
    process_steps = (
        summary_si.get("process_steps")
        or consultation.get("process_steps")
        or []
    )
    step_contents = [
        s.get("description") or s.get("name") or str(s)
        for s in process_steps
        if isinstance(s, dict)
    ]

    return {
        "problem": _pick("problem", "problem_to_solve"),
        "solution": _pick("solution", "means_for_solving", "core_technology"),
        "difference": _pick("differentiators", "differentiation"),
        "effect": _pick("expected_effects", "effect", "effects"),
        "algorithm_steps": step_contents,
        "claim_1": claim_1_text,
        "dependent_claims": dependent_texts,
        "drawings": drawing_list,
    }


# ── 출력 변환 ─────────────────────────────────────────────────────────

def _build_raw_output(spec: dict) -> dict:
    """generate_specification 결과 → SpecificationAgentOutput 형식의 raw dict.

    specification_agent.py는 DB 컬럼명(tech_field, problem_statement, ...)을 사용하지만
    SpecificationAgentOutput은 state.py 필드명(technical_field, problem_to_solve, ...)을 사용한다.
    """
    return {
        "status": "ok",
        "summary": "발명의 설명 초안 생성 완료",
        "technical_field": spec.get("tech_field", ""),
        "background_art": spec.get("background_art", ""),
        "problem_to_solve": spec.get("problem_statement", ""),
        "means_for_solving": spec.get("solution_means", ""),
        "effects": spec.get("effects", ""),
        "brief_description_of_drawings": spec.get("drawing_description", ""),
        "detailed_description": spec.get("detailed_desc", ""),
        "notes": [spec["embodiments"]] if spec.get("embodiments") else [],
    }


# ── LangGraph 노드 ─────────────────────────────────────────────────────

def specification_node(state: dict) -> dict:
    """LangGraph 노드 함수.

    입력: state["summary"] 또는 state["consultation"], state["claims"], state["drawings"]
    출력: state["specification"] ← SpecificationAgentOutput.model_dump()
          state["workflow"]

    어떤 state가 들어와도 예외를 바깥으로 던지지 않는다.
    실패 시 hard fallback SpecificationAgentOutput 반환.
    """
    workflow = state.get("workflow") or {}
    errors: list[str] = list(workflow.get("errors") or [])

    data = _extract_invention_data(state)
    if not data["problem"] and not data["claim_1"]:
        errors.append("specification_node: 발명 정보(problem, claim) 없음")
        fallback = _FALLBACK.model_copy()
        fallback.warnings.append("발명 정보 없음 — 상담/청구항 결과 확인 필요")
        return {
            "specification": fallback.model_dump(),
            "workflow": {
                **workflow,
                "errors": errors,
                "current_agent": "specification",
                "next_agent": "composer",
            },
        }

    raw_output: dict = {}
    try:
        spec = generate_specification(data)
        raw_output = _build_raw_output(spec)
    except Exception as e:
        errors.append(f"specification_node: generate_specification 실패 — {e}")
        raw_output = {
            "status": "failed",
            "summary": f"발명의 설명 생성 실패: {e}",
            "technical_field": "",
            "background_art": "",
            "problem_to_solve": data.get("problem", ""),
            "means_for_solving": data.get("solution", ""),
            "effects": data.get("effect", ""),
            "brief_description_of_drawings": "",
            "detailed_description": "",
        }

    validated = safe_validate_output(
        agent_name="specification",
        schema=SpecificationAgentOutput,
        raw_output=raw_output,
        fallback=_FALLBACK,
    )

    return {
        "specification": validated.model_dump(),
        "workflow": {
            **workflow,
            "errors": errors,
            "current_agent": "specification",
            "next_agent": "composer",
        },
    }
