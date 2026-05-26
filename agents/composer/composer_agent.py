from typing import Any, Dict

from .adapters import (
    get_claim_1_text,
    get_all_claims_text,
    get_drawings,
    select_representative_drawing,
    get_specification_sections,
)
from .validators import validate_composer_inputs
from .abstract_generator import generate_abstract_from_claim_1
from .docx_writer import create_final_docx, build_output_docx_path

def run_composer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Validate inputs
    validate_composer_inputs(state)
    
    # 2. Extraction
    claim_1_text = get_claim_1_text(state)
    all_claims_text = get_all_claims_text(state)
    spec_sections = get_specification_sections(state)
    drawings = get_drawings(state)
    
    # 3. Generate abstract
    abstract_text = generate_abstract_from_claim_1(claim_1_text)
    
    # 4. Select representative drawing
    rep_drawing_path = select_representative_drawing(state)
    
    # 5. Create final docx
    final_docx_path = build_output_docx_path(state)
    create_final_docx(
        output_path=final_docx_path,
        abstract_text=abstract_text,
        representative_drawing_path=rep_drawing_path,
        claims_text=all_claims_text,
        spec_sections=spec_sections,
        drawings=drawings
    )
    
    # 6. Update state
    if "final_package" not in state:
        state["final_package"] = {}
        
    state["final_package"]["rendered_docx_path"] = final_docx_path
    state["final_package"]["abstract_text"] = abstract_text
    state["final_package"]["representative_drawing_path"] = rep_drawing_path
    state["final_package"]["sections_order"] = [
        "abstract",
        "representative_drawing",
        "claims",
        "specification",
        "drawings",
    ]
    
    state["final_docx_path"] = final_docx_path
    state["abstract_text"] = abstract_text
    state["representative_drawing_path"] = rep_drawing_path
    
    return state
