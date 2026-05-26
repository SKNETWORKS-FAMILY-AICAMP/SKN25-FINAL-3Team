import re
from typing import Any, Dict, List, Optional

def sanitize_filename(value: str) -> str:
    # Remove invalid filename characters
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', str(value))

def get_first_non_empty(source_dict: Dict[str, Any], keys: List[str]) -> str:
    for key in keys:
        val = source_dict.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return ""

def _extract_claim_text_from_dict(claim_dict: Dict[str, Any]) -> str:
    return get_first_non_empty(claim_dict, ["text", "claim_text", "content", "claim"])

def get_claim_1_text(state: Dict[str, Any]) -> str:
    if state.get("claim_1_text") and str(state["claim_1_text"]).strip():
        return str(state["claim_1_text"]).strip()
    
    claims_obj = state.get("claims")
    if isinstance(claims_obj, list) and len(claims_obj) > 0:
        first_claim = claims_obj[0]
        if isinstance(first_claim, dict):
            text = _extract_claim_text_from_dict(first_claim)
            if text:
                return text
        else:
            if str(first_claim).strip():
                return str(first_claim).strip()
                
    elif isinstance(claims_obj, dict):
        draft_claims = claims_obj.get("draft_claims", [])
        if isinstance(draft_claims, list) and len(draft_claims) > 0:
            first_claim = draft_claims[0]
            if isinstance(first_claim, dict):
                text = _extract_claim_text_from_dict(first_claim)
                if text:
                    return text
            else:
                if str(first_claim).strip():
                    return str(first_claim).strip()
            
    if state.get("claims_text"):
        match = re.search(r"【청구항 1】(.*?)(?:【청구항 2】|$)", str(state["claims_text"]), re.DOTALL)
        if match and match.group(1).strip():
            return match.group(1).strip()
        if str(state["claims_text"]).strip():
            return str(state["claims_text"]).strip()
        
    raise ValueError("청구항 1항을 찾을 수 없습니다.")

def get_all_claims_text(state: Dict[str, Any]) -> str:
    if state.get("claims_text") and str(state["claims_text"]).strip():
        return str(state["claims_text"]).strip()
        
    claims_obj = state.get("claims")
    claims_list = []
    
    if isinstance(claims_obj, list):
        claims_list = claims_obj
    elif isinstance(claims_obj, dict):
        draft_claims = claims_obj.get("draft_claims", [])
        if isinstance(draft_claims, list):
            claims_list = draft_claims
            
    if claims_list:
        texts = []
        for i, c in enumerate(claims_list):
            if isinstance(c, dict):
                text = _extract_claim_text_from_dict(c)
                if not text:
                    continue
                claim_no = c.get("claim_no", i + 1)
                texts.append(f"【청구항 {claim_no}】\n{text}")
            else:
                text = str(c).strip()
                if not text:
                    continue
                texts.append(f"【청구항 {i+1}】\n{text}")
                
        result = "\n\n".join(texts)
        if result.strip():
            return result.strip()
            
    raise ValueError("청구항 전체 내용을 찾을 수 없습니다.")

def get_drawings(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    drawings_obj = state.get("drawings")
    if isinstance(drawings_obj, list):
        return drawings_obj
        
    if isinstance(drawings_obj, dict) and "figures" in drawings_obj and isinstance(drawings_obj["figures"], list):
        return drawings_obj["figures"]
        
    image_paths = state.get("drawing_image_paths")
    if isinstance(image_paths, list):
        converted = []
        for i, path in enumerate(image_paths):
            if path:
                converted.append({
                    "figure_no": f"도 {i+1}",
                    "description": "",
                    "image_path": str(path)
                })
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
    if drawings and len(drawings) > 0:
        return get_drawing_image_path(drawings[0])
    return None

def get_specification_sections(state: Dict[str, Any]) -> Dict[str, str]:
    spec_obj = state.get("specification_sections")
    if isinstance(spec_obj, dict):
        return spec_obj
    
    spec_obj = state.get("specification")
    if isinstance(spec_obj, dict):
        return spec_obj
        
    return {}
