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


# drawing_rules.yaml figure_types 키 → FigureType Literal 매핑
_DTYPE_TO_FIGURE_TYPE = {
    "flowchart": "flowchart",
    "method": "flowchart",
    "process": "flowchart",
    "block_diagram": "system_architecture",
    "sequence": "sequence",
    "stateDiagram": "other",
    "ui_screen": "ui",
    "data_flow": "data_flow",
}


def _consultation_to_text(c: dict) -> str:
    """ConsultationState → drawing_agent의 extract_components()가 읽을 수 있는 텍스트.

    기존 drawing_agent는 특허 txt 파일을 파싱해서 동작한다.
    상담 에이전트 결과(구조화 JSON)를 그 형식에 맞는 텍스트로 변환한다.
    """
    parts = []
    if c.get("invention_title"): parts.append(f"발명의 명칭: {c['invention_title']}")
    if c.get("background"):      parts.append(f"배경기술: {c['background']}")
    if c.get("problem"):         parts.append(f"해결하려는 과제: {c['problem']}")
    if c.get("solution"):        parts.append(f"과제의 해결 수단: {c['solution']}")
    if c.get("effect"):          parts.append(f"발명의 효과: {c['effect']}")

    comps = c.get("components", [])
    if comps:
        parts.append("\n발명의 상세한 설명")
        for comp in comps:
            parts.append(f"{comp.get('name', '')}은(는) {comp.get('role', '')}을(를) 수행한다.")

    steps = c.get("process_steps", [])
    if steps:
        parts.append("\n처리 단계")
        for step in sorted(steps, key=lambda s: s.get("order", 0)):
            parts.append(
                f"단계 {step.get('order', '')}: {step.get('name', '')} - {step.get('description', '')}"
            )

    # 부호의 설명 형식으로 구성요소 번호 부여
    # drawing_rules.yaml: system_level_start=100, component_increment=10
    if comps:
        parts.append("\n부호의 설명")
        for i, comp in enumerate(comps):
            parts.append(f"{100 + i * 10}: {comp.get('name', '')}")

    parts.append("\n도면의 간단한 설명")
    parts.append("도 1은 전체 시스템 구성도이다.")
    if steps:
        parts.append("도 2는 처리 흐름도이다.")

    return "\n".join(parts)


def _build_drawing_state(results: list, analysis: dict) -> dict:
    """DrawingResult list + analysis → DrawingState dict.

    drawing_rules.yaml 참조부호 정책:
    - system_level_start: 100
    - component_increment: 10
    - 동일 구성요소는 모든 도면에서 같은 번호 사용
    """
    comps = analysis.get("components", [])

    ref_numerals: dict = {}
    for i, comp in enumerate(comps):
        num = str(100 + i * 10)
        ref_numerals[num] = {
            "number": num,
            "term": comp.get("name", ""),
            "figure": "",
            "component_id": str(comp.get("component_id", "")).strip() or num,
            "description": comp.get("description", ""),
        }

    figures = []
    for r in results:
        nums = re.findall(r"\d+", r.fig_number)
        fig_no = int(nums[0]) if nums else 0
        fig_comps, fig_steps = [], []

        if r.fig_json_path and Path(r.fig_json_path).exists():
            try:
                with open(r.fig_json_path, encoding="utf-8") as f:
                    fig_json = json.load(f)
                elements = fig_json.get("elements", [])
                if r.diagram_type in ("flowchart", "method", "process"):
                    fig_steps = [e.get("name", "") for e in elements if e.get("name")]
                else:
                    fig_comps = [e.get("name", "") for e in elements if e.get("name")]
                # 참조부호에 도면 번호 채우기
                for e in elements:
                    rn = str(e.get("ref_no", "")).strip()
                    if rn in ref_numerals:
                        ref_numerals[rn]["figure"] = r.fig_number
            except Exception:
                pass

        figures.append({
            "fig_no": fig_no,
            "title": r.diagram_title,
            "type": _DTYPE_TO_FIGURE_TYPE.get(r.diagram_type, "other"),
            "purpose": r.diagram_title,
            "components": fig_comps,
            "steps": fig_steps,
            "description": r.diagram_title,
        })

    avg_score = sum(r.quality_score for r in results) / max(1, len(results))
    return {
        "figures": figures,
        "reference_numerals": ref_numerals,
        "drawing_notes": [
            f"총 {len(results)}개 도면 생성",
            f"평균 품질 점수: {avg_score:.1f}점",
            "drawing_rules.yaml 정책 적용: 100단위 시작, 10 증가",
        ],
    }


def _build_doc_links(results: list, state: dict, ref_numerals: dict) -> dict:
    """results + ref_numerals → DocumentLinksState 부분 업데이트.

    drawing_rules.yaml 요구사항:
    - reference_numeral_map ↔ drawings.reference_numerals 동기화 필수
    - 각 figure 구성요소 → consultation 구성요소 링크 생성
    """
    comps = state.get("consultation", {}).get("components", [])

    fig_links = []
    for r in results:
        if not (r.fig_json_path and Path(r.fig_json_path).exists()):
            continue
        try:
            with open(r.fig_json_path, encoding="utf-8") as f:
                fig_json = json.load(f)
            for e in fig_json.get("elements", []):
                ename = e.get("name", "")
                if not ename:
                    continue
                for comp in comps:
                    cname = comp.get("name", "")
                    if cname and (ename in cname or cname in ename):
                        fig_links.append({
                            "source": f"drawings.figures[{r.fig_number}].{ename}",
                            "target": f"consultation.components.{comp.get('id', '')}",
                            "relation": "refers_to",
                            "evidence": f"{r.fig_number}의 구성요소 {ename}",
                            "confidence": 0.8,
                            "review_flag": "",
                        })
                        break
        except Exception:
            pass

    existing = state.get("document_links", {})
    return {
        **existing,
        "reference_numeral_map": ref_numerals,
        "figure_to_component_links": existing.get("figure_to_component_links", []) + fig_links,
    }


def _load_analysis(output_dir: str, app_num: str) -> dict:
    """generate_all_drawings가 저장한 patent_analysis.json을 읽는다."""
    try:
        with open(Path(output_dir) / app_num / "patent_analysis.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def drawing_node(state: dict) -> dict:
    """LangGraph 노드 함수. PatentAgentState를 받아 drawings + document_links를 채운다.

    입력: state["consultation"] (상담 에이전트 결과)
    출력: state["drawings"], state["document_links"], state["workflow"] 업데이트
    """
    consultation = state.get("consultation", {})
    if not consultation:
        workflow = state.get("workflow", {})
        return {
            "workflow": {
                **workflow,
                "errors": [*workflow.get("errors", []), "drawing_node: consultation 데이터 없음"],
            }
        }

    app_num = re.sub(r"[^A-Za-z0-9_-]", "_", consultation.get("invention_title", "unknown"))[:40]
    output_dir = "drawing_analysis"

    results = generate_all_drawings(_consultation_to_text(consultation), app_num, output_dir)
    analysis = _load_analysis(output_dir, app_num)

    drawing_state = _build_drawing_state(results, analysis)
    doc_links = _build_doc_links(results, state, drawing_state["reference_numerals"])

    workflow = state.get("workflow", {})
    return {
        "drawings": drawing_state,
        "document_links": doc_links,
        "workflow": {**workflow, "current_agent": "drawing", "next_agent": "specification"},
    }
