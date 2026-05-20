"""LangGraph 노드 연결부. drawing_agent.py의 기존 로직을 State 기반으로 감싼다.

drawing_agent.py는 건드리지 않는다.
이 파일만 LangGraph 그래프 조립 시 import한다.

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


# drawing_agent diagram_type → state.py FigureType Literal 매핑
_DTYPE_TO_FIGURE_TYPE = {
    "flowchart":    "flowchart",
    "method":       "flowchart",
    "process":      "flowchart",
    "block_diagram":"system_architecture",
    "sequence":     "sequence",
    "stateDiagram": "other",
    "ui_screen":    "ui",
    "data_flow":    "data_flow",
}

# 빈 DrawingState — 에러 시 반환하는 안전한 기본값
_EMPTY_DRAWING_STATE: dict = {
    "figures": [],
    "reference_numerals": {},
    "drawing_notes": [],
}


# ── 입력 변환 ──────────────────────────────────────────────────────────

def _state_to_invention_text(consultation: dict) -> str:
    """ConsultationState dict → drawing_agent가 받는 특허 텍스트 형식.

    drawing_agent.py는 특허 txt 파일 형식의 텍스트를 기대한다.
    consultation에 없는 필드는 조용히 건너뛴다.
    """
    parts: list[str] = []

    if consultation.get("invention_title"):
        parts.append(f"발명의 명칭: {consultation['invention_title']}")
    if consultation.get("background"):
        parts.append(f"배경기술: {consultation['background']}")
    if consultation.get("problem"):
        parts.append(f"해결하려는 과제: {consultation['problem']}")
    if consultation.get("solution"):
        parts.append(f"과제의 해결 수단: {consultation['solution']}")
    if consultation.get("effect"):
        parts.append(f"발명의 효과: {consultation['effect']}")

    comps = consultation.get("components") or []
    if comps:
        parts.append("\n발명의 상세한 설명")
        for c in comps:
            name = c.get("name", "")
            role = c.get("role", "")
            if name:
                parts.append(f"{name}은(는) {role}을(를) 수행한다." if role else f"{name}.")

    steps = consultation.get("process_steps") or []
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


def _safe_app_num(consultation: dict) -> str:
    """consultation에서 안전한 app_num을 생성한다. 비어있어도 'unknown'으로 처리."""
    raw = consultation.get("invention_title") or "unknown"
    return re.sub(r"[^A-Za-z0-9_-]", "_", raw)[:40] or "unknown"


# ── 출력 변환 ──────────────────────────────────────────────────────────

def _build_drawing_state(results: list, analysis: dict) -> dict:
    """DrawingResult list + patent_analysis → DrawingState dict.

    state.py 기준:
        DrawingState.figures           : list[FigureSpec]
        DrawingState.reference_numerals: dict[str, ReferenceNumeral]
        DrawingState.drawing_notes     : list[str]
    """
    # 참조부호 — LLM이 추출한 구성요소 기준 (100단위)
    ref_numerals: dict = {}
    for i, comp in enumerate(analysis.get("components", [])):
        num = str(100 + i * 10)
        ref_numerals[num] = {
            "number":       num,
            "term":         comp.get("name", ""),
            "figure":       "",
            "component_id": str(comp.get("component_id", "")).strip() or num,
            "description":  comp.get("description", ""),
        }

    # 도면 목록 — DrawingResult → FigureSpec
    figures: list = []
    for r in results:
        nums   = re.findall(r"\d+", r.fig_number)
        fig_no = int(nums[0]) if nums else 0
        fig_comps: list[str] = []
        fig_steps: list[str] = []

        if r.fig_json_path and Path(r.fig_json_path).exists():
            try:
                with open(r.fig_json_path, encoding="utf-8") as f:
                    fig_json = json.load(f)
                elements = fig_json.get("elements", [])

                if r.diagram_type in ("flowchart", "method", "process"):
                    fig_steps = [e["name"] for e in elements if e.get("name")]
                else:
                    fig_comps = [e["name"] for e in elements if e.get("name")]

                # 참조부호에 첫 등장 도면 번호 기록
                for e in elements:
                    rn = str(e.get("ref_no", "")).strip()
                    if rn in ref_numerals and not ref_numerals[rn]["figure"]:
                        ref_numerals[rn]["figure"] = r.fig_number
            except Exception:
                pass

        figures.append({
            "fig_no":     fig_no,
            "title":      r.diagram_title,
            "type":       _DTYPE_TO_FIGURE_TYPE.get(r.diagram_type, "other"),
            "purpose":    r.diagram_title,
            "components": fig_comps,
            "steps":      fig_steps,
            "description": r.diagram_title,
        })

    avg_score = (
        sum(r.quality_score for r in results) / len(results) if results else 0
    )
    return {
        "figures": figures,
        "reference_numerals": ref_numerals,
        "drawing_notes": [
            f"총 {len(results)}개 도면 생성",
            f"평균 품질 점수: {avg_score:.1f}점",
            f"참조부호 {len(ref_numerals)}개",
        ],
    }


def _load_analysis(output_dir: str, app_num: str) -> dict:
    """generate_all_drawings가 저장한 patent_analysis.json을 읽는다."""
    try:
        path = Path(output_dir) / app_num / "patent_analysis.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── LangGraph 노드 ─────────────────────────────────────────────────────

def drawing_node(state: dict) -> dict:
    """LangGraph 노드 함수. PatentAgentState를 받아 drawings + document_links를 채운다.

    입력: state["consultation"] (ConsultationState)
    출력: state["drawings"]       (DrawingState)
          state["document_links"]
          state["workflow"]

    어떤 state가 들어와도 예외를 바깥으로 던지지 않는다.
    실패 시 빈 DrawingState + workflow.errors에 메시지를 기록한다.
    """
    workflow     = state.get("workflow") or {}
    consultation = state.get("consultation") or {}
    errors: list[str] = list(workflow.get("errors") or [])

    # consultation이 완전히 비었으면 빈 state 반환
    if not consultation:
        errors.append("drawing_node: consultation 데이터 없음")
        return {
            "drawings":       _EMPTY_DRAWING_STATE,
            "document_links": state.get("document_links") or {},
            "workflow":       {**workflow, "errors": errors,
                               "current_agent": "drawing", "next_agent": "specification"},
        }

    output_dir = "drawing_analysis"
    app_num    = _safe_app_num(consultation)
    text       = _state_to_invention_text(consultation)

    results: list = []
    try:
        results = generate_all_drawings(text, app_num, output_dir)
    except Exception as e:
        errors.append(f"drawing_node: generate_all_drawings 실패 — {e}")

    analysis = _load_analysis(output_dir, app_num)

    drawing_state = (
        _build_drawing_state(results, analysis)
        if results
        else {**_EMPTY_DRAWING_STATE,
              "drawing_notes": ["도면 생성 결과 없음 — workflow.errors 확인"]}
    )

    # document_links: reference_numeral_map 동기화
    existing_links = state.get("document_links") or {}
    doc_links = {
        **existing_links,
        "reference_numeral_map": drawing_state["reference_numerals"],
    }

    return {
        "drawings":       drawing_state,
        "document_links": doc_links,
        "workflow": {
            **workflow,
            "errors":        errors,
            "current_agent": "drawing",
            "next_agent":    "specification",
        },
    }
