import os
import fitz  # PyMuPDF
from docx import Document
import olefile
import zlib
import base64

def extract_text_from_pdf(file_path):
    """PDF에서 텍스트 추출 (PyMuPDF)"""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_docx(file_path):
    """DOCX에서 텍스트 추출 (python-docx)"""
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

import re

def extract_text_from_hwp(file_path):
    """HWP(V5)에서 텍스트 추출 (olefile & zlib)"""
    try:
        f = olefile.OleFileIO(file_path)
        dirs = f.listdir()

        bodytext_dirs = [d for d in dirs if d[0] == 'BodyText']
        if not bodytext_dirs:
            return "HWP 파일 구조가 예상과 다릅니다. (BodyText 없음)"

        full_text = ""
        for d in bodytext_dirs:
            section_name = "/".join(d)
            stream = f.openstream(section_name)
            data = stream.read()
            
            try:
                unpacked_data = zlib.decompress(data, -15)
            except:
                unpacked_data = data
            
            section_text = unpacked_data.decode('utf-16', errors='ignore')
            full_text += section_text
        
        f.close()
        
        # 제어 문자 제거 (AI 분석 품질 향상)
        clean_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', full_text)
        return clean_text.strip()
    except Exception as e:
        return f"[오류: HWP 직접 추출 실패. PDF로 변환하여 업로드해주세요. 상세:{str(e)}]"

def extract_images_from_pdf(file_path, output_dir="temp_imgs"):
    """PDF에서 이미지(도면 등)만 따로 추출"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    image_paths = []
    with fitz.open(file_path) as doc:
        for i, page in enumerate(doc):
            image_list = page.get_images()
            for j, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                img_path = f"{output_dir}/p{i}_img{j}.{ext}"
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                image_paths.append(img_path)
    return image_paths

def encode_image_to_base64(image_path):
    """이미지를 base64로 인코딩 (Vision API용)"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
