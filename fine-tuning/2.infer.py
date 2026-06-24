import os
import json
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# ==========================================
# 1. 설정 (경로 세팅)
# ==========================================
BASE_MODEL_NAME = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"
LORA_OUTPUT_DIR = "outputs/exaone-patent-clarity-qlora"  # 학습 완료된 outputs 폴더 경로

TEST_INPUT_FILE = "final_ft_test.jsonl"         # 보유 중이신 Test 세트 파일명
TEST_OUTPUT_FILE = "test_predictions.jsonl"  # 추론 결과가 저장될 파일명

MAX_SEQ_LENGTH = 8192


# ==========================================
# 2. 모델 및 토크나이저 로드 (추론 최적화)
# ==========================================
def load_model_for_inference():
    print("토크나이저 로드 중...")
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_NAME, # 🎯 LORA_OUTPUT_DIR 대신 베이스 모델에서 가져옵니다!
        revision="496aef060b296b34c6b0035149f5af9e2b8c168c", # 리비전도 잊지 말고 챙겨주세요
        trust_remote_code=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    print("베이스 모델 로드 중 (4-bit 양자화)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        revision="496aef060b296b34c6b0035149f5af9e2b8c168c",  # 이 줄을 반드시 추가
        quantization_config=bnb_config,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True
    )

    print("LoRA 가중치 병합 중...")
    model = PeftModel.from_pretrained(base_model, LORA_OUTPUT_DIR)
    model.eval() # 추론 모드 전환
    
    return model, tokenizer

# ==========================================
# 3. 추론 실행부
# ==========================================
def run_inference():
    model, tokenizer = load_model_for_inference()
    
    # Test 데이터 로드
    with open(TEST_INPUT_FILE, "r", encoding="utf-8") as f:
        test_rows = [json.loads(line) for line in f if line.strip()]
        
    print(f"총 {len(test_rows)}개의 Test 데이터 추론을 시작합니다.")
    
    with open(TEST_OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for idx, row in enumerate(tqdm(test_rows, desc="Inferencing")):
            messages = row.get("messages", [])
            
            # 정답(Assistant) 대화는 제외하고 System과 User 질문만 추출하여 프롬프트 구성
            inference_messages = [m for m in messages if m["role"] in ["system", "user"]]
            
            # Chat Template 적용 (add_generation_prompt=True로 모델이 답변하도록 유도)
            prompt_text = tokenizer.apply_chat_template(
                inference_messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            inputs = tokenizer(
                prompt_text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=MAX_SEQ_LENGTH
            ).to("cuda")
            
            # 텍스트 생성 파라미터 조율 (JSON 스키마 보존을 위해 과도한 자유도 제한)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=4096,
                    do_sample=False,        # Greedy Search로 항상 일관된 논리 출력 유도
                    temperature=0.0,
                    eos_token_id=tokenizer.eos_token_id,
                    pad_token_id=tokenizer.pad_token_id
                )
            
            # 생성된 답변 토큰만 잘라내어 디코딩
            generated_ids = outputs[0][inputs.input_ids.shape[1]:]
            response_text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
            
            # 평가 스크립트 규격과 호환되도록 정답 구조와 동일한 형태의 JSONL로 저장
            result_data = {
                "messages": inference_messages + [{"role": "assistant", "content": response_text}]
            }
            f_out.write(json.dumps(result_data, ensure_ascii=False) + "\n")
            
    print(f"추론 완료! 결과가 {TEST_OUTPUT_FILE}에 저장되었습니다.")

if __name__ == "__main__":
    run_inference()