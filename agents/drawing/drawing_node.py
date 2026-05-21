"""LangGraph 노드 연결부. drawing_agent.py의 기존 로직을 State 기반으로 감싼다.

drawing_agent.py는 건드리지 않는다.
이 파일만 LangGraph 그래프 조립 시 import한다.

출력 schema: agents/schemas/drawing.py DrawingAgentOutput
저장 위치  : state["drawings"]

사용 예:
    from agents.drawing.drawing_node import drawing_node

    graph.add_node("drawing", drawing_node)
    graph.add_edge("drawing", "specification")
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from agents.drawing.drawing_agent import generate_all_drawings
from agents.schemas.drawing import DrawingAgentOutput, FigureDraft, ReferenceNumeral
from agents.validation import safe_validate_output


# diagram_type → FigureType 매핑
_DTYPE_MAP = {
    "flowchart":    "flowchart",
    "method":       "flowchart",
    "process":      "flowchart",
    "block_diagram":"system_architecture",
    "sequence":     "sequence",
    "stateDiagram": "other",
    "ui_screen":    "ui",
    "data_flow":    "data_flow",
}

# hard fallback — 파이프라인이 죽지 않도록
_FALLBACK = DrawingAgentOutput(
    status="failed",
    summary="도면 생성 실패 — hard fallback",
    figures=[],
    reference_numerals=[],
    drawing_notes=[],
)


# ── 입력 변환 ──────────────────────────────────────────────────────────

def _resolve_invention_source(state: dict) -> dict:
    """summary.structured_invention 우선, 없으면 consultation 폴백."""
    si = (state.get("summary") or {}).get("structured_invention") or {}
    if si:
        return si
    return state.get("consultation") or {}


def _state_to_invention_text(src: dict) -> str:
    """ConsultationState 또는 structured_invention → drawing_agent가 받는 특허 텍스트."""
    parts: list[str] = []

    title = src.get("invention_title") or src.get("title")
    if title:
        parts.append(f"발명의 명칭: {title}")
    if src.get("background"):
        parts.append(f"배경기술: {src['background']}")
    problem = src.get("problem") or src.get("problem_to_solve")
    if problem:
        parts.append(f"해결하려는 과제: {problem}")
    solution = src.get("solution") or src.get("means_for_solving") or src.get("core_technology")
    if solution:
        parts.append(f"과제의 해결 수단: {solution}")
    effect = src.get("effect") or src.get("expected_effects")
    if effect:
        parts.append(f"발명의 효과: {effect}")

    comps = src.get("components") or []
    if comps:
        parts.append("\n발명의 상세한 설명")
        for c in comps:
            name = c.get("name", "")
            role = c.get("role", "")
            if name:
                parts.append(f"{name}은(는) {role}을(를) 수행한다." if role else f"{name}.")

    steps = src.get("process_steps") or []
    if steps:
        parts.append("\n처리 단계")
        for s in sorted(steps, key=lambda x: x.get("order", 0)):
            order = s.get("order", "")
            name  = s.get("name", "")
            desc  = s.get("description", "")
            parts.append(f"단계 {order}: {name}" + (f" - {desc}" if desc else ""))

    if comps:
        parts.append("\n부호의 설명")
        for i, c in enumerate(comps):
            parts.append(f"{100 + i * 10}: {c.get('name', '')}")

    parts.append("\n도면의 간단한 설명")
    parts.append("도 1은 전체 시스템 구성도이다.")
    if steps:
        parts.append("도 2는 처리 흐름도이다.")

    return "\n".join(parts)


def _safe_app_num(src: dict) -> str:
    raw = src.get("invention_title") or src.get("title") or "unknown"
    return re.sub(r"[^A-Za-z0-9_-]", "_", raw)[:40] or "unknown"


# ── 출력 변환 (DrawingAgentOutput 스키마 기준) ────────────────────────

def _build_raw_output(results: list, analysis: dict) -> dict:
    """DrawingResult + analysis → DrawingAgentOutput 형식의 raw dict.

    DrawingAgentOutput 스키마 기준:
        figures           : list[FigureDraft]   fig_no=str
        reference_numerals: list[ReferenceNumeral]  number/label/description/component_id
        drawing_notes     : list[str]
        status / summary  : 공통 AgentOutputBase 필드
    """
    # 참조부호 — list[ReferenceNumeral] 형식 (dict 아님)
    ref_numerals: list[dict] = []
    for i, comp in enumerate(analysis.get("components", [])):
        num = str(100 + i * 10)
        ref_numerals.append({
            "number":       num,
            "label":        comp.get("name", ""),          # term → label
            "description":  comp.get("description", ""),
            "component_id": str(comp.get("component_id", "")).strip() or num,
        })

    # 도면 목록 — list[FigureDraft] 형식 (fig_no=str)
    figures: list[dict] = []
    for r in results:
        nums    = re.findall(r"\d+", r.fig_number)
        fig_no  = nums[0] if nums else "1"               # int → str
        comps: list[str] = []

        if r.fig_json_path and Path(r.fig_json_path).exists():
            try:
                with open(r.fig_json_path, encoding="utf-8") as f:
                    fig_json = json.load(f)
                elements = fig_json.get("elements", [])
                comps = [e["name"] for e in elements if e.get("name")]
            except Exception:
                pass

        figures.append({
            "fig_no":      fig_no,
            "title":       r.diagram_title,
            "type":        _DTYPE_MAP.get(r.diagram_type, "other"),
            "components":  comps,
            "description": r.diagram_title,
        })

    avg_score = sum(r.quality_score for r in results) / max(1, len(results))
    return {
        "status":            "ok",
        "summary":           f"도면 {len(figures)}개 생성 완료 (평균 {avg_score:.0f}점)",
        "figures":           figures,
        "reference_numerals": ref_numerals,
        "drawing_notes":     [
            f"총 {len(figures)}개 도면 생성",
            f"평균 품질 점수: {avg_score:.1f}점",
            f"참조부호 {len(ref_numerals)}개",
        ],
    }


def _load_analysis(output_dir: str, app_num: str) -> dict:
    try:
        with open(Path(output_dir) / app_num / "patent_analysis.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── LangGraph 노드 ─────────────────────────────────────────────────────

def drawing_node(state: dict) -> dict:
    """LangGraph 노드 함수.

    입력: state["summary"]["structured_invention"] 우선, 없으면 state["consultation"]
    출력: state["drawings"] ← DrawingAgentOutput.model_dump()
          state["workflow"]

    어떤 state가 들어와도 예외를 바깥으로 던지지 않는다.
    실패 시 hard fallback DrawingAgentOutput 반환.
    """
    workflow = state.get("workflow") or {}
    errors: list[str] = list(workflow.get("errors") or [])

    src = _resolve_invention_source(state)
    if not src:
        errors.append("drawing_node: 발명 데이터 없음 (summary.structured_invention, consultation 모두 비어있음)")
        fallback = _FALLBACK.model_copy()
        fallback.warnings.append("발명 데이터 없음")
        return {
            "drawings": fallback.model_dump(),
            "workflow": {**workflow, "errors": errors,
                         "current_agent": "drawing", "next_agent": "specification"},
        }

    output_dir = "drawing_analysis"
    app_num    = _safe_app_num(src)
    text       = _state_to_invention_text(src)

    results: list = []
    try:
        results = generate_all_drawings(text, app_num, output_dir)
    except Exception as e:
        errors.append(f"drawing_node: generate_all_drawings 실패 — {e}")

    analysis = _load_analysis(output_dir, app_num)

    raw_output = (
        _build_raw_output(results, analysis)
        if results
        else {"status": "failed", "summary": "도면 생성 결과 없음",
              "figures": [], "reference_numerals": [], "drawing_notes": []}
    )

    validated = safe_validate_output(
        agent_name="drawing",
        schema=DrawingAgentOutput,
        raw_output=raw_output,
        fallback=_FALLBACK,
    )

    return {
        "drawings": validated.model_dump(),
        "workflow": {
            **workflow,
            "errors":        errors,
            "current_agent": "drawing",
            "next_agent":    "specification",
        },
    }
