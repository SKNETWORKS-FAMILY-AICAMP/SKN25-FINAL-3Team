import os, base64, glob, json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import fitz

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PDF_DIRS = ["patent_pdfs/G06F", "patent_pdfs/G06N", "patent_pdfs/G06Q", "patent_pdfs/G06V"]
OUTPUT_DIR = "drawing_analysis"
MIN_IMAGE_SIZE = 5000

def extract_images_from_pdf(pdf_path):
    images = []
    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            for img_idx, img_info in enumerate(page.get_images(full=True)):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                if len(img_bytes) < MIN_IMAGE_SIZE:
                    continue
                ext = base_image["ext"]
                if ext not in ["png", "jpeg", "jpg"]:
                    ext = "png"
                images.append({"page": page_num+1, "index": img_idx, "base64": base64.b64encode(img_bytes).decode(), "ext": ext, "size": len(img_bytes)})
        doc.close()
    except Exception as e:
        print(f"[오류] {pdf_path}: {e}")
    return images

def analyze_drawing(image_b64, ext, title=""):
    prompt = f"""특허 도면을 분석해줘.{f' 특허: {title}' if title else ''}
1. 도면 유형: (구성도/흐름도/회로도/그래프/기타)
2. 주요 구성요소:
3. 동작 원리:
4. 핵심 기술 키워드: (3~5개)"""
    try:
        res = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{image_b64}", "detail": "high"}},
                {"type": "text", "text": prompt}
            ]}],
            max_tokens=500
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"[분석 오류] {e}"

def run_batch(pdf_dirs=PDF_DIRS, limit=47):
    all_pdfs = []
    for d in pdf_dirs:
        all_pdfs += glob.glob(os.path.join(d, "*.pdf"))
    print(f"=== 도면 Agent 시작 === 총 {len(all_pdfs)}개 → {limit}건 처리")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for pdf_path in all_pdfs[:limit]:
        app_num = Path(pdf_path).stem
        out = os.path.join(OUTPUT_DIR, f"{app_num}_drawings.json")
        if os.path.exists(out):
            print(f"[스킵] {app_num} (이미 분석됨)")
            continue
        print(f"\n[처리 중] {app_num}")
        images = extract_images_from_pdf(pdf_path)
        print(f"  도면 {len(images)}개 추출")
        drawings = []
        for i, img in enumerate(images):
            print(f"  → 도면 {i+1}/{len(images)} 분석 중...")
            drawings.append({"page": img["page"], "analysis": analyze_drawing(img["base64"], img["ext"])})
        result = {"app_num": app_num, "drawings": drawings}
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  저장: {out}")
    print("\n=== 완료 ===")

if __name__ == "__main__":
    run_batch(limit=47)