import os
import json
import torch
from dataclasses import dataclass
from typing import Any, Dict, List

from datasets import Dataset, DatasetDict
from huggingface_hub import login
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
)
from peft import (
    LoraConfig,
    prepare_model_for_kbit_training,
    get_peft_model,
)

# 빠른 HF 다운로드
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"


# ==========================================
# 1. Data Collator
# ==========================================
@dataclass
class DataCollatorForCausalLMWithLabels:
    tokenizer: Any
    pad_to_multiple_of: int = 8

    def __call__(self, features: List[Dict[str, List[int]]]) -> Dict[str, torch.Tensor]:
        max_len = max(len(f["input_ids"]) for f in features)

        if self.pad_to_multiple_of:
            max_len = (
                (max_len + self.pad_to_multiple_of - 1)
                // self.pad_to_multiple_of
            ) * self.pad_to_multiple_of

        batch = {
            "input_ids": [],
            "attention_mask": [],
            "labels": [],
        }

        for f in features:
            pad_len = max_len - len(f["input_ids"])

            batch["input_ids"].append(
                f["input_ids"] + [self.tokenizer.pad_token_id] * pad_len
            )
            batch["attention_mask"].append(
                f["attention_mask"] + [0] * pad_len
            )
            batch["labels"].append(
                f["labels"] + [-100] * pad_len
            )

        return {
            k: torch.tensor(v, dtype=torch.long)
            for k, v in batch.items()
        }


# ==========================================
# 2. 설정
# ==========================================
CONFIG = {
    "hf_token": ".",
    "wandb_api_key": ".",

    "model_name": "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct",
    "model_revision": "496aef060b296b34c6b0035149f5af9e2b8c168c",

    "train_file": "final_ft_train.jsonl",
    "val_file": "final_ft_val.jsonl",
    "output_dir": "outputs/exaone-patent-clarity-qlora",

    "max_seq_length": 8192,
    "num_train_epochs": 5.0,
    "learning_rate": 2e-4,

    "per_device_train_batch_size": 1,
    "per_device_eval_batch_size": 1,
    "gradient_accumulation_steps": 16,

    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,

    "logging_steps": 10,
    "eval_steps": 50,
    "save_steps": 50,
    "save_total_limit": 2,

    "use_wandb": True,
    "wandb_project": "patent-exaone-clarity-ft2",
    "wandb_run_name": "exaone-7.8b-qlora-full-seq2",

    "attn_implementation": "sdpa",
    "seed": 42,
}


DATASET_SYSTEM_PROMPT = """당신은 대한민국 특허청(KIPO) 소속의 컴퓨터·인공지능(AI) 분야 베테랑 특허 심사관입니다. 제시된 [청구범위]를 아래의 법령 및 심사지침에 의거하여 엄격하게 심사하고, 그 결과를 지정된 JSON 스키마 형식으로 출력하십시오.

---
[심사 기준: 특허법 제42조 제4항 제2호 (명확성)]
- 청구항은 발명이 명확하고 간결하게 적혀 있어야 합니다.
- 판단 기준: '통상의 기술자'가 출원 당시의 '기술상식'을 고려하여, 발명의 설명이나 도면을 참작했을 때 청구범위로부터 특허받고자 하는 발명을 명확하게 파악할 수 있는지 개별적으로 판단합니다. 

[AI/소프트웨어 분야 핵심 거절 기준 (Rejection Rules)]
1. 구성요소 간 결합관계 부재: 각 구성요소(모듈, 데이터, 인프라 등)가 단순히 나열되어 있을 뿐, 이들 간의 시계열적 처리 관계나 유기적 결합관계가 기재되지 않아 발명이 불명확한 경우 거절합니다.
2. 기능적 표현의 한계: AI/BM 발명 특성상 기능이나 효과 위주로 청구항이 기재된 경우, 발명의 설명과 도면을 참작하더라도 그 기능적 표현의 의미 내용을 명확하게 확정할 수 없다면 발명이 불명확한 것으로 봅니다. 
3. 수치한정 및 모호한 표현: '주로', '많은', '높은', '대략' 등 비교 기준이 불명확한 표현을 사용하거나, 수치한정 발명에서 상한/하한이 없는 모호한 기재로 권리범위를 불명확하게 한 경우 거절합니다.
4. 카테고리 불비 및 중복 기재: 독립항의 카테고리(예: 방법)와 이를 인용하는 종속항의 카테고리(예: 장치, CRM)가 서로 달라 인용관계가 모호하거나, 동일 내용이 너무 장황하게 중복 기재된 경우 거절합니다. 

[오기 구제 가이드라인 (거절 예외 조항)]
- 의미상 대응: 지시하는 문언과 지시대상이 완전히 일치하지 않더라도, 발명의 설명을 참작하여 의미상 서로 대응됨이 명확히 알 수 있는 경우 적법한 기재로 봅니다.

---
[출력 규칙]
- 반드시 아래의 정확한 JSON 구조(Schema)를 지켜서 출력해야 하며, 이 외의 다른 키(Key)나 텍스트를 절대 추가하지 마십시오.
{
  "examiner_result": {
    "is_approved": true 또는 false,
    "rejections": [
      {
        "claims": [지적된 청구항 번호 숫자 리스트],
        "reason_text": "의견서 톤의 거절 이유 원문 텍스트"
      }
    ]
  }
}
- 심사 결과 기재불비 사항이 발견되면 전체 'examiner_result.is_approved'를 반드시 'false'로 설정하고, rejections 배열에 청구항 번호, 의견서 톤의 거절 이유(reason_text)를 작성하십시오.
- 결격 사유가 전혀 없다면 'is_approved'를 'true'로, 'rejections'는 빈 배열 '[]'로 출력하십시오.
- 결격 사유가 여러 개 발견되는 경우, 각각의 사유에 대해 별도의 항목으로 'rejections' 배열에 추가하십시오. 이때, 각 항목의 'claims'에는 해당 사유가 지적된 청구항 번호를 숫자 리스트로 작성하고, 'reason_text'에는 의견서 톤의 거절 이유 원문 텍스트를 작성하십시오.
- 내용이 '삭제' 또는 '삭제항'인 청구항은 분석 대상에서 완전히 제외하고 claims 배열에 포함하지 마십시오."""


# ==========================================
# 3. 데이터 로딩
# ==========================================
def load_dataset_safely(train_file: str, val_file: str) -> DatasetDict:
    def load_jsonl(path: str):
        dataset = []
        skipped = 0

        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if not line.strip():
                    continue

                try:
                    dataset.append(json.loads(line))
                except Exception as e:
                    skipped += 1
                    print(f"⚠️ JSONL skip: {path}:{line_no} / {e}")

        print(f"Loaded {path}: {len(dataset)} rows / skipped={skipped}")
        return dataset

    train_data = load_jsonl(train_file)
    val_data = load_jsonl(val_file)

    if not train_data:
        raise RuntimeError("train 데이터가 비어 있습니다.")

    if not val_data:
        raise RuntimeError("validation 데이터가 비어 있습니다.")

    return DatasetDict({
        "train": Dataset.from_list(train_data),
        "validation": Dataset.from_list(val_data),
    })


# ==========================================
# 4. 토크나이징
# ==========================================
def tokenize_example(example: Dict[str, Any], tokenizer):
    messages = example.get("messages", [])

    if not any(m.get("role") == "system" for m in messages):
        messages.insert(0, {
            "role": "system",
            "content": DATASET_SYSTEM_PROMPT,
        })

    full_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    prompt_messages = [
        m for m in messages
        if m.get("role") in ["system", "user"]
    ]

    prompt_text = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    full_ids = tokenizer(
        full_text,
        add_special_tokens=False,
        truncation=True,
        max_length=CONFIG["max_seq_length"],
    )["input_ids"]

    prompt_ids = tokenizer(
        prompt_text,
        add_special_tokens=False,
        truncation=True,
        max_length=CONFIG["max_seq_length"],
    )["input_ids"]

    labels = full_ids.copy()

    prompt_len = min(len(prompt_ids), len(labels))
    labels[:prompt_len] = [-100] * prompt_len

    return {
        "input_ids": full_ids,
        "attention_mask": [1] * len(full_ids),
        "labels": labels,
    }


# ==========================================
# 5. 메인 학습
# ==========================================
def main():
    torch.manual_seed(CONFIG["seed"])

    hf_token = CONFIG["hf_token"].strip()
    wandb_key = CONFIG["wandb_api_key"].strip()

    login(token=hf_token)

    if CONFIG["use_wandb"]:
        os.environ["WANDB_API_KEY"] = wandb_key
        os.environ["WANDB_PROJECT"] = CONFIG["wandb_project"]
        os.environ["WANDB_NAME"] = CONFIG["wandb_run_name"]

        import wandb
        wandb.login(key=wandb_key)

    tokenizer = AutoTokenizer.from_pretrained(
        CONFIG["model_name"],
        revision=CONFIG["model_revision"],
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dataset = load_dataset_safely(
        CONFIG["train_file"],
        CONFIG["val_file"],
    )

    tokenized = dataset.map(
        lambda x: tokenize_example(x, tokenizer),
        remove_columns=dataset["train"].column_names,
    )

    model = AutoModelForCausalLM.from_pretrained(
        CONFIG["model_name"],
        revision=CONFIG["model_revision"],
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
        device_map="auto",
        trust_remote_code=True,
        attn_implementation=CONFIG["attn_implementation"],
    )

    model = prepare_model_for_kbit_training(model)

    model = get_peft_model(
        model,
        LoraConfig(
            r=CONFIG["lora_r"],
            lora_alpha=CONFIG["lora_alpha"],
            lora_dropout=CONFIG["lora_dropout"],
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=[
                "attn.q_proj",
                "attn.k_proj",
                "attn.v_proj",
                "attn.out_proj",
                "mlp.c_fc1",
                "mlp.c_fc2",
                "mlp.c_proj",
            ],
        ),
    )

    model.print_trainable_parameters()

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=CONFIG["output_dir"],

            num_train_epochs=CONFIG["num_train_epochs"],
            learning_rate=CONFIG["learning_rate"],

            per_device_train_batch_size=CONFIG["per_device_train_batch_size"],
            per_device_eval_batch_size=CONFIG["per_device_eval_batch_size"],
            gradient_accumulation_steps=CONFIG["gradient_accumulation_steps"],

            bf16=True,
            optim="paged_adamw_8bit",
            gradient_checkpointing=True,

            logging_steps=CONFIG["logging_steps"],

            eval_strategy="steps",
            eval_steps=CONFIG["eval_steps"],

            save_strategy="steps",
            save_steps=CONFIG["save_steps"],
            save_total_limit=CONFIG["save_total_limit"],

            report_to="wandb" if CONFIG["use_wandb"] else "none",
            run_name=CONFIG["wandb_run_name"] if CONFIG["use_wandb"] else None,

            seed=CONFIG["seed"],
        ),
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=DataCollatorForCausalLMWithLabels(tokenizer),
    )

    trainer.train()
    trainer.save_model(CONFIG["output_dir"])

    if CONFIG["use_wandb"]:
        import wandb
        wandb.finish()


if __name__ == "__main__":
    main()