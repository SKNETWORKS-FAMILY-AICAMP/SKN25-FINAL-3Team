from typing import Any, Dict

from .abstract_generator import generate_abstract_from_claim_1
from .adapters import (
    get_all_claims_text,
    get_claim_1_text,
    get_drawings,
    get_first_non_empty,
    get_specification_sections,
    select_representative_drawing,
)
from .docx_writer import build_output_docx_path, create_final_docx, render_markdown
from .validators import validate_composer_inputs


def _get_title(state: Dict[str, Any]) -> str:
    summary = state.get("summary") or {}
    title = summary.get("project_name") or summary.get("title")
    if title and str(title).strip():
        return str(title).strip()

    title = state.get("title")
    if title and str(title).strip():
        return str(title).strip()

    return "특허 명세서"


def _build_composer_notes(state: Dict[str, Any]) -> list[str]:
    notes = []
    if state.get("document_links"):
        notes.append("document_links는 일관성 점검용으로만 참고했습니다.")
    if state.get("invention_graph"):
        notes.append("invention_graph는 일관성 점검용으로만 참고했습니다.")
    if state.get("drafting_options"):
        notes.append("drafting_options는 문체와 작성 옵션의 참고용으로만 사용했습니다.")

    composer_state = state.get("composer") or {}
    existing_notes = composer_state.get("composer_notes")
    if isinstance(existing_notes, list):
        notes.extend(str(item) for item in existing_notes if str(item).strip())

    return notes


def run_composer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    validate_composer_inputs(state)

    summary = state.get("summary") or {}
    prior_art = state.get("prior_art") or {}
    claims = state.get("claims") or {}
    drawings = state.get("drawings") or {}
    specification = get_specification_sections(state)
    document_links = state.get("document_links") or {}
    invention_graph = state.get("invention_graph") or {}
    drafting_options = state.get("drafting_options") or {}

    if not isinstance(drawings, dict):
        drawings = {
            "figures": get_drawings(state),
            "reference_numerals": {},
            "drawing_notes": [],
        }

    if not isinstance(claims, dict):
        claims = {"draft_claims": []}

    if not isinstance(specification, dict):
        specification = {}

    claim_1_text = get_claim_1_text(state)
    claims_text = get_all_claims_text(state)
    claim_drafts = claims.get("draft_claims", [])

    if not isinstance(claim_drafts, list):
        claim_drafts = []

    problem = get_first_non_empty(
        specification,
        ["problem_to_solve", "problem", "summary_problem", "해결하려는 과제"],
    )
    solution = get_first_non_empty(
        specification,
        ["means_for_solving", "solution", "summary_solution", "과제의 해결수단", "과제의 해결 수단"],
    )
    effect = get_first_non_empty(
        specification,
        ["effects", "effect", "summary_effect", "발명의 효과"],
    )

    abstract_text = generate_abstract_from_claim_1(
        claim_1_text=claim_1_text,
        invention_title=summary.get("project_name") or summary.get("title") or state.get("title"),
        problem=problem,
        solution=solution,
        effect=effect,
    )

    representative_drawing_path = select_representative_drawing(state)
    final_docx_path = build_output_docx_path(state)

    create_final_docx(
        output_path=final_docx_path,
        abstract_text=abstract_text,
        representative_drawing_path=representative_drawing_path,
        claims=claim_drafts,
        claims_text=claims_text,
        spec_sections=specification,
        drawings=get_drawings(state),
    )

    rendered_markdown = render_markdown(
        title=_get_title(state),
        abstract_text=abstract_text,
        representative_drawing_path=representative_drawing_path,
        claims_text=claims_text,
        specification=specification,
        drawings=get_drawings(state),
    )

    composer_notes = _build_composer_notes(state)
    unresolved_items = []
    sections = {
        "abstract": abstract_text,
        "claims": claims_text,
        "specification": "\n".join(
            f"{key}: {value}" for key, value in specification.items() if isinstance(value, str) and value.strip()
        ),
        "drawings": "\n".join(
            f"{key}: {value}" for key, value in drawings.items() if isinstance(value, str) and value.strip()
        ),
    }

    final_package = {
        "status": "ok",
        "summary": f"{_get_title(state)} 최종 패키지가 생성되었습니다.",
        "warnings": [],
        "notes": composer_notes,
        "evidence": [],
        "details": {
            "docx_path": final_docx_path,
            "representative_drawing_path": representative_drawing_path,
        },
        "title": _get_title(state),
        "abstract": abstract_text,
        "sections": sections,
        "claims": claim_drafts,
        "drawings": drawings,
        "specification": specification,
        "prior_art_report": prior_art,
        "rendered_markdown": rendered_markdown,
        "rendered_docx_path": final_docx_path,
        "rendered_html_path": None,
        "unresolved_items": unresolved_items,
        "composer_notes": composer_notes,
    }

    state["final_package"] = final_package
    state["final_docx_path"] = final_docx_path
    state["abstract_text"] = abstract_text
    state["representative_drawing_path"] = representative_drawing_path
    state["rendered_markdown"] = rendered_markdown
    state["title"] = final_package["title"]
    state["summary"] = summary
    state["claims"] = claims
    state["drawings"] = drawings
    state["specification"] = specification
    state["prior_art"] = prior_art
    state["document_links"] = document_links
    state["invention_graph"] = invention_graph
    state["drafting_options"] = drafting_options

    return final_package
