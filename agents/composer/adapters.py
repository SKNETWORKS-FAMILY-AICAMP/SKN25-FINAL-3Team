import re
from typing import Any, Dict, List, Optional


def sanitize_filename(value: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', str(value))


def get_first_non_empty(source_dict: Dict[str, Any], keys: List[str]) -> str:
    for key in keys:
        val = source_dict.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def _extract_claim_text_from_dict(claim_dict: Dict[str, Any]) -> str:
    return get_first_non_empty(claim_dict, ["text", "claim_text", "content", "claim"])


CLAIM_1_PATTERN = re.compile(r"【청구항\s*1】(.*?)(?:【청구항\s*2】|$)", re.DOTALL)


def _get_claims_collection(state: Dict[str, Any]) -> List[Any]:
    claims_obj = state.get("claims")
    if isinstance(claims_obj, list):
        return claims_obj

    if isinstance(claims_obj, dict):
        draft_claims = claims_obj.get("draft_claims")
        if isinstance(draft_claims, list):
            return draft_claims

    return []


def get_claim_1_text(state: Dict[str, Any]) -> str:
    if state.get("claim_1_text") and str(state["claim_1_text"]).strip():
        return str(state["claim_1_text"]).strip()

    for first_claim in _get_claims_collection(state):
        if isinstance(first_claim, dict):
            text = _extract_claim_text_from_dict(first_claim)
            if text:
                return text
        elif str(first_claim).strip():
            return str(first_claim).strip()

    if state.get("claims_text"):
        claims_text = str(state["claims_text"]).strip()
        match = CLAIM_1_PATTERN.search(claims_text)
        if match and match.group(1).strip():
            return match.group(1).strip()

        raise ValueError("claims_text에서 【청구항 1】을 추출할 수 없습니다.")

    raise ValueError("청구항 1항을 찾을 수 없습니다.")


def get_all_claims_text(state: Dict[str, Any]) -> str:
    draft_claims = _get_claims_collection(state)
    if draft_claims:
        texts = []
        for i, claim in enumerate(draft_claims):
            if isinstance(claim, dict):
                text = _extract_claim_text_from_dict(claim)
                if not text:
                    continue
                claim_no = claim.get("claim_no", i + 1)
                texts.append(f"【청구항 {claim_no}】\n{text}")
            else:
                text = str(claim).strip()
                if not text:
                    continue
                texts.append(f"【청구항 {i + 1}】\n{text}")

        result = "\n\n".join(texts)
        if result.strip():
            return result.strip()

    if state.get("claims_text") and str(state["claims_text"]).strip():
        return str(state["claims_text"]).strip()

    raise ValueError("청구항 전체 내용을 찾을 수 없습니다.")


def get_drawings(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    drawings_obj = state.get("drawings")
    if isinstance(drawings_obj, dict) and isinstance(drawings_obj.get("figures"), list):
        return drawings_obj["figures"]

    if isinstance(drawings_obj, list):
        return drawings_obj

    image_paths = state.get("drawing_image_paths")
    if isinstance(image_paths, list):
        converted = []
        for i, path in enumerate(image_paths):
            if path:
                converted.append(
                    {
                        "figure_no": f"도 {i + 1}",
                        "description": "",
                        "image_path": str(path),
                    }
                )
        return converted

    return []


def get_drawing_image_path(drawing: Dict[str, Any]) -> Optional[str]:
    keys_to_check = ["image_path", "png_path", "jpg_path", "jpeg_path", "svg_path"]
    for key in keys_to_check:
        val = drawing.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return None


def select_representative_drawing(state: Dict[str, Any]) -> Optional[str]:
    drawings = get_drawings(state)
    if drawings:
        return get_drawing_image_path(drawings[0])
    return None


def get_specification_sections(state: Dict[str, Any]) -> Dict[str, str]:
    spec_obj = state.get("specification")
    if isinstance(spec_obj, dict):
        return spec_obj

    spec_obj = state.get("specification_sections")
    if isinstance(spec_obj, dict):
        return spec_obj

    return {}
