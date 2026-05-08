import os, glob, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_steps_from_claim(claim_text: str) -> str:
    prompt = f"""다음 특허 청구항에서 방법/단계를 추출해서 Mermaid 흐름도로 변환해줘.

청구항:
{claim_text[:2000]}

규칙:
- "A단계, B단계, C단계를 포함하는 방법" → flowchart TD 형식
- 단계가 없으면 구성요소를 노드로 표현
- 한국어 그대로 사용
- Mermaid 코드만 출력 (```없이)

예시 출력:
flowchart TD
    A[사용자 요청 수신] --> B[LLM 분석]
    B --> C[응답 생성]
    C --> D[피드백 수집]"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500
    )
    return res.choices[0].message.content.strip()

def process_patent_txt(txt_file: str) -> dict:
    with open(txt_file, "r", encoding="utf-8-sig") as f:
        text = f.read()
    
    # 청구범위 추출
    claim = ""
    if "청구범위" in text:
        start = text.find("청구범위")
        end = text.find("발명의 내용", start)
        if end == -1:
            end = start + 2000
        claim = text[start:end].strip()
    
    if not claim:
        return None
    
    app_num = os.path.basename(txt_file).replace(".txt", "")
    mermaid = extract_steps_from_claim(claim)
    
    return {
        "app_num": app_num,
        "mermaid": mermaid
    }

def run(limit=5):
    os.makedirs("flowcharts", exist_ok=True)
    txt_files = []
    for d in ["G06F", "G06N", "G06Q", "G06V"]:
        txt_files += glob.glob(f"{d}/*.txt")
    
    print(f"총 {len(txt_files)}개 → {limit}건 처리")
    
    for txt_file in txt_files[:limit]:
        result = process_patent_txt(txt_file)
        if not result:
            continue
        print(f"\n[{result['app_num']}]")
        print(result['mermaid'])
        out = f"flowcharts/{result['app_num']}.mmd"
        with open(out, "w", encoding="utf-8") as f:
            f.write(result['mermaid'])
        print(f"저장: {out}")

if __name__ == "__main__":
    run(limit=542)