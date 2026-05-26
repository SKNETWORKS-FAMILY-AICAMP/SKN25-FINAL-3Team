import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from docx import Document
from docx.shared import Inches
from .adapters import get_drawing_image_path, sanitize_filename

SECTION_MAPPING = [
    ("【기술분야】", ["technical_field", "기술분야"]),
    ("【발명(고안)의 배경이 되는 기술】", ["background_art", "background", "배경기술"]),
    ("【해결하려는 과제】", ["problem_to_solve", "problem", "summary_problem", "해결하려는 과제"]),
    ("【과제의 해결 수단】", ["means_for_solving", "solution", "summary_solution", "과제의 해결수단", "과제의 해결 수단"]),
    ("【발명(고안)의 효과】", ["effects", "effect", "summary_effect", "발명의 효과"]),
    ("【도면의 간단한 설명】", ["brief_description_of_drawings", "brief_drawings", "도면의 간단한 설명"]),
    ("【발명(고안)을 실시하기 위한 구체적인 내용】", ["detailed_description", "embodiment", "구체적인 실시예", "구체적인 내용"]),
]

def is_supported_docx_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in [
        ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff"
    ]

def add_image_or_placeholder(doc: Document, image_path: Optional[str], width_inches: float = 6.0) -> None:
    if not image_path:
        doc.add_paragraph("[이미지 없음]")
        return

    if not os.path.exists(image_path):
        doc.add_paragraph(f"[이미지 파일을 찾을 수 없습니다: {image_path}]")
        return

    if not is_supported_docx_image(image_path):
        doc.add_paragraph(f"[Word에 직접 삽입할 수 없는 이미지 형식입니다: {image_path}]")
        return

    try:
        doc.add_picture(image_path, width=Inches(width_inches))
    except Exception as e:
        doc.add_paragraph(f"[이미지 삽입 실패: {e}]")

def build_output_docx_path(state: Dict[str, Any]) -> str:
    os.makedirs("outputs", exist_ok=True)
    user_id = sanitize_filename(str(state.get("user_id", "user")))
    consultation_idx = sanitize_filename(str(state.get("consultation_idx", "session")))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"final_patent_specification_{user_id}_{consultation_idx}_{timestamp}.docx"
    return os.path.abspath(os.path.join("outputs", filename))

def add_specification_sections(doc: Document, spec_sections: Dict[str, str]) -> None:
    # 1. 기술분야 및 배경기술
    for title, keys in SECTION_MAPPING[:2]:
        content = ""
        for key in keys:
            if spec_sections.get(key) and str(spec_sections[key]).strip():
                content = str(spec_sections[key]).strip()
                break
        if content:
            doc.add_paragraph(title)
            doc.add_paragraph(content)
            
    # 2. 발명(고안)의 내용 묶음
    doc.add_paragraph("【발명(고안)의 내용】")
    for title, keys in SECTION_MAPPING[2:5]: # 과제, 해결수단, 효과
        content = ""
        for key in keys:
            if spec_sections.get(key) and str(spec_sections[key]).strip():
                content = str(spec_sections[key]).strip()
                break
        if content:
            doc.add_paragraph(title)
            doc.add_paragraph(content)
            
    # 3. 도면 간단한 설명 및 구체적인 내용
    for title, keys in SECTION_MAPPING[5:]:
        content = ""
        for key in keys:
            if spec_sections.get(key) and str(spec_sections[key]).strip():
                content = str(spec_sections[key]).strip()
                break
        if content:
            doc.add_paragraph(title)
            doc.add_paragraph(content)

def create_final_docx(
    output_path: str,
    abstract_text: str,
    representative_drawing_path: Optional[str],
    claims_text: str,
    spec_sections: Dict[str, str],
    drawings: List[Dict[str, Any]]
) -> None:
    doc = Document()
    
    # 1. 요약
    doc.add_heading("요약", level=1)
    doc.add_paragraph(abstract_text)
    doc.add_page_break()
    
    # 2. 대표도
    doc.add_heading("대표도", level=1)
    if representative_drawing_path:
        add_image_or_placeholder(doc, representative_drawing_path)
    else:
        doc.add_paragraph("대표도 없음")
    doc.add_page_break()
    
    # 3. 청구항/청구범위
    doc.add_heading("청구항", level=1)
    if "【청구범위】" not in claims_text:
        doc.add_paragraph("【청구범위】")
    doc.add_paragraph(claims_text)
    doc.add_page_break()
    
    # 4. 발명의 설명
    doc.add_heading("발명의 설명", level=1)
    add_specification_sections(doc, spec_sections)
    doc.add_page_break()
    
    # 5. 도면
    doc.add_heading("도면", level=1)
    for i, drawing in enumerate(drawings):
        fig_no = drawing.get("figure_no", drawing.get("fig_no", i + 1))
        if isinstance(fig_no, int) or str(fig_no).isdigit():
            fig_str = f"【도 {fig_no}】"
        else:
            if str(fig_no).startswith("도 "):
                fig_str = f"【{fig_no}】"
            else:
                fig_str = f"【도 {fig_no}】"
                
        doc.add_paragraph(fig_str)
        
        desc = drawing.get("description", "")
        if desc:
            doc.add_paragraph(desc)
            
        img_path = get_drawing_image_path(drawing)
        add_image_or_placeholder(doc, img_path)
        doc.add_paragraph("")
        
    doc.save(output_path)
