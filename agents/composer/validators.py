from typing import Any, Dict
from .adapters import (
    get_claim_1_text,
    get_all_claims_text,
    get_specification_sections,
    get_drawings
)

def validate_composer_inputs(state: Dict[str, Any]) -> None:
    claim_1_text = ""
    try:
        claim_1_text = get_claim_1_text(state)
    except ValueError as e:
        raise ValueError(f"청구항 1항 오류: {e}")

    if not claim_1_text.strip():
        raise ValueError("청구항 1항이 비어 있습니다.")

    claims_text = ""
    try:
        claims_text = get_all_claims_text(state)
    except ValueError as e:
        raise ValueError(f"청구항 전체 내용 오류: {e}")

    if not claims_text.strip():
        raise ValueError("청구항 전체 내용이 비어 있습니다.")

    spec_sections = get_specification_sections(state)
    if not spec_sections:
        raise ValueError("발명의 설명 섹션을 찾을 수 없습니다.")

    spec_candidate_keys = [
        "technical_field", "기술분야",
        "background_art", "background", "배경기술",
        "problem_to_solve", "problem", "summary_problem", "해결하려는 과제",
        "means_for_solving", "solution", "summary_solution", "과제의 해결수단", "과제의 해결 수단",
        "effects", "effect", "summary_effect", "발명의 효과",
        "brief_description_of_drawings", "brief_drawings", "도면의 간단한 설명",
        "detailed_description", "embodiment", "구체적인 실시예", "구체적인 내용",
    ]

    if not any(str(spec_sections.get(k, "")).strip() for k in spec_candidate_keys):
        raise ValueError("발명의 설명에 사용할 수 있는 내용이 없습니다.")

    drawings = get_drawings(state)
    if not drawings:
        raise ValueError("대표도 및 도면 생성을 위한 도면 정보가 없습니다.")
