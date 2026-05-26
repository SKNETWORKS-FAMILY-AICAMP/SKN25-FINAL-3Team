import os
import sys

# Add backend or base directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from docx import Document
from agents.composer.composer_agent import run_composer_agent
import agents.composer.composer_agent

def mock_generate_abstract_from_claim_1(claim_1_text: str) -> str:
    return "본 발명은 머신러닝을 이용해 피싱 사이트를 탐지하는 장치 및 방법에 관한 것으로서, 새로운 패턴의 피싱 사이트도 효과적으로 탐지할 수 있다."

def run_test():
    agents.composer.composer_agent.generate_abstract_from_claim_1 = mock_generate_abstract_from_claim_1
    # Mocking state according to the requested features
    mock_state = {
        "claim_1_text": "본 발명은 머신러닝 기반의 피싱 사이트 탐지 장치에 관한 것이다.",
        "claims_text": "【청구항 1】\n본 발명은 머신러닝 기반의 피싱 사이트 탐지 장치에 관한 것이다.\n【청구항 2】\n제 1항에 있어서...",
        "specification_sections": {
            "technical_field": "본 발명은 피싱 사이트 탐지 기술에 관한 것이다.",
            "background_art": "종래에는 규칙 기반 탐지가 주를 이루었다.",
            "problem_to_solve": "하지만 신종 피싱 사이트 탐지율이 낮다.",
            "means_for_solving": "머신러닝 앙상블 모델을 적용한다.",
            "effects": "새로운 패턴의 피싱 사이트도 효과적으로 탐지할 수 있다.",
            "brief_description_of_drawings": "도 1은 전체 시스템 구성도이다.",
            "detailed_description": "구체적인 실시예를 살펴보면 다음과 같다..."
        },
        "drawings": [
            {
                "figure_no": "도 1",
                "description": "도 1은 본 발명의 일 실시예에 따른 시스템 블록도이다.",
                "image_path": "dummy_img1.png"
            }
        ],
        "final_package": {}
    }

    # Set dummy env variable to a smaller or default model for fast testing
    # Or just rely on default.
    os.environ["COMPOSER_MODEL"] = "gpt-4o-mini"
    
    # We won't actually have a real dummy_img1.png, but the code handles exceptions.
    
    # Run agent
    print("Running Composer Agent...")
    try:
        updated_state = run_composer_agent(mock_state)
    except Exception as e:
        print(f"Agent failed: {e}")
        return

    docx_path = updated_state.get("final_docx_path")
    print(f"Docx generated at: {docx_path}")
    
    if not os.path.exists(docx_path):
        print("FAIL: final docx was not created.")
        return

    # Verify constraints
    doc = Document(docx_path)
    text_content = []
    
    paragraphs = []
    for p in doc.paragraphs:
        if p.text.strip():
            paragraphs.append(p.text.strip())
            text_content.append(p.text.strip())

    full_text = "\n".join(text_content)
    
    print("\n--- Verifying Constraints ---")

    # Constraint 1 & 2: Exclude specific terms
    if "【발명(고안)의 설명】" in full_text:
        print("FAIL: 【발명(고안)의 설명】 should not be included.")
    else:
        print("PASS: 【발명(고안)의 설명】 is correctly excluded.")
        
    if "【발명(고안)의 명칭】" in full_text:
        print("FAIL: 【발명(고안)의 명칭】 should not be included.")
    else:
        print("PASS: 【발명(고안)의 명칭】 is correctly excluded.")
        
    # Constraint 3: "발명의 설명" directly followed by "【기술분야】"
    for i, p in enumerate(paragraphs):
        if p == "발명의 설명":
            if i + 1 < len(paragraphs) and paragraphs[i+1] == "【기술분야】":
                print("PASS: '발명의 설명' is immediately followed by '【기술분야】'.")
            else:
                next_p = paragraphs[i+1] if i + 1 < len(paragraphs) else "<END_OF_DOC>"
                print(f"FAIL: '발명의 설명' is followed by '{next_p}', not '【기술분야】'.")
            break

    # Constraint 4: Order of sections
    headings = ["요약", "대표도", "청구항", "발명의 설명", "도면"]
    indices = []
    for h in headings:
        try:
            idx = paragraphs.index(h)
            indices.append(idx)
        except ValueError:
            print(f"FAIL: Heading '{h}' not found.")
            indices.append(-1)
            
    is_sorted = True
    for i in range(len(indices)-1):
        if indices[i] == -1 or indices[i+1] == -1 or indices[i] >= indices[i+1]:
            is_sorted = False
            
    if is_sorted:
        print("PASS: Document sections are correctly ordered.")
    else:
        print(f"FAIL: Document sections are incorrectly ordered. Indices: {indices}")
        
    print("\n--- Completed Verification ---")

if __name__ == "__main__":
    run_test()
