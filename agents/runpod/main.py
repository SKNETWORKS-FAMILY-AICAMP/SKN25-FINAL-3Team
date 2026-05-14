# pip install fastapi uvicorn pydantic python-dotenv
# uvicorn main:app --host 0.0.0.0 --port 8000

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from openai import OpenAI

# .env 파일 로드
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI(title="Patent Claim Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_MODEL_NAME = "LGAI-EXAONE/EXAONE-3.0-7.8B-Instruct"
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
LORA_HF_REPO = os.getenv("LORA_HF_REPO", "silverstone1004/claim") 

tokenizer = None
model = None

@app.on_event("startup")
def load_model():
    global tokenizer, model
    print("모델과 토크나이저를 불러오는 중입니다...")

    try:
        tokenizer = AutoTokenizer.from_pretrained(LORA_HF_REPO, token=HF_TOKEN, use_fast=False)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME, token=HF_TOKEN, use_fast=False)

    model_kwargs = {
        "device_map": "auto",
        "trust_remote_code": True,
        "token": HF_TOKEN
    }
    if torch.cuda.is_available():
        model_kwargs["torch_dtype"] = torch.bfloat16

    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_NAME, **model_kwargs)
    
    # HF Hub에서 LoRA 직접 로드
    model = PeftModel.from_pretrained(base_model, LORA_HF_REPO, token=HF_TOKEN)
    model.eval()
    print("✅ 모델 준비 완료!")

# --- API 요청/응답 데이터 규격 ---
class ClaimRequest(BaseModel):
    consultation_note: str

class ClaimResponse(BaseModel):
    status: str
    claim_1: str
    dependent_claims: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

def generate_text(prompt: str, max_tokens: int = 1024) -> str:
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id
        )
    generated_ids = outputs[0][inputs['input_ids'].shape[1]:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

@app.post("/generate-claims", response_model=ClaimResponse)
def generate_claims(request: ClaimRequest):
    if tokenizer is None or model is None:
        raise HTTPException(status_code=503, detail="로컬 모델 로딩 중")

    try:
        # [Step 1] 파인튜닝 모델로 제1항(독립항) 생성
        prompt_1 = f"###상담 노트:\n{request.consultation_note}\n\n### 지시사항:\n다음 내용을 바탕으로 특허 청구항 제1항(독립항) 하나만 작성하세요. 응답은 오직 청구항 1항 문장으로 구성하세요.\n\n### 제1항:"
        
        claim_1_result = generate_text(prompt_1)

        # [Step 2] OpenAI API로 나머지 종속항 생성
        system_prompt = (
            "당신은 전문 특허 변리사입니다. 사용자가 제공한 제1항(독립항)과 발명 정보를 바탕으로, "
            "발명을 구체화하는 나머지 종속항들을 생성해 주세요. "
            "각 청구항은 '제N항에 있어서,' 로 시작해야 하며, 오직 청구항 문장들만 출력하세요."
        )
        
        user_prompt = f"### 상담 노트:\n{request.consultation_note}\n\n### 제1항(독립항):\n{claim_1_result}\n\n위 제1항을 바탕으로 종속항(제2항부터)들을 작성해 주세요."

        # OpenAI API 호출 (비용 효율적인 gpt-4o-mini 모델 추천)
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        
        dependent_claims_result = completion.choices[0].message.content.strip()

        return ClaimResponse(
            status="success", 
            claim_1=claim_1_result, 
            dependent_claims=dependent_claims_result
        )
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"청구항 생성 중 에러가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)