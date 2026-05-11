# consultation_agent.py
"""
상담 에이전트 MVP
흐름: 사용자 발명 설명 → invention.json 생성 + 부족 정보 질문
"""

import os
import json
import re
import uuid
import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

# ──────────────────────────────────────────
# invention.json 스키마 정의
# ──────────────────────────────────────────

INVENTION_SCHEMA = {
    "invention_title": None,      # 발명 명칭
    "technical_field": None,      # 기술 분야
    "problem": None,              # 해결하려는 문제
    "solution": None,             # 핵심 해결 수단
    "key_components": [],         # 구성요소 목록
    "process_steps": [],          # 처리 단계 (방법 발명)
    "effect": None,               # 발명 효과
    "keywords": [],               # 검색 키워드 (선행기술조사 전달)
}

# 필수 필드 (이게 없으면 질문 생성)
REQUIRED_FIELDS = ["invention_title", "technical_field", "problem", "solution", "key_components", "keywords"]

# 필드별 질문 템플릿
QUESTIONS = {
    "invention_title":  "발명의 이름이나 명칭을 한 줄로 표현하면 어떻게 될까요?",
    "technical_field":  "이 발명은 어떤 기술 분야에 속하나요? (예: 인공지능, 반도체, 의료기기, 소프트웨어 등)",
    "problem":          "기존에 어떤 불편함이나 한계가 있어서 이 발명을 하게 되셨나요?",
    "solution":         "그 문제를 어떻게 해결했나요? 핵심 아이디어나 방법을 설명해주세요.",
    "key_components":   "발명을 구성하는 주요 부품이나 기능 요소가 무엇인가요? (예: 센서, 서버, 앱, 알고리즘 등)",
    "process_steps":    "발명이 동작하는 순서를 단계별로 설명해주실 수 있나요?",
    "effect":           "이 발명을 사용하면 어떤 점이 좋아지거나 개선되나요?",
    "keywords":         "이 발명과 관련된 핵심 키워드를 3~5개 알려주세요.",
}


# ──────────────────────────────────────────
# completeness_score 계산
# ──────────────────────────────────────────

def calc_score(invention: dict) -> float:
    """필수 필드 기준 완성도 계산 (0.0 ~ 1.0)"""
    filled = 0
    for field in REQUIRED_FIELDS:
        val = invention.get(field)
        if val and val != [] and val is not None:
            filled += 1
    return round(filled / len(REQUIRED_FIELDS), 2)


def get_missing_fields(invention: dict) -> list:
    """비어있는 필수 필드 목록 반환"""
    missing = []
    for field in REQUIRED_FIELDS:
        val = invention.get(field)
        if not val or val == []:
            missing.append(field)
    return missing


# ──────────────────────────────────────────
# LLM: 발화 → invention.json 초안 생성
# ──────────────────────────────────────────

EXTRACT_SYSTEM = """당신은 사용자의 발명 설명을 듣고 특허 명세서 작성을 위한 구조화된 JSON을 만드는 전문가입니다.

사용자 발화에서 아래 JSON 형식으로 추출하세요. 알 수 없는 필드는 null 또는 빈 배열로 두세요.
절대 추측해서 채우지 마세요. 사용자가 말한 내용만 반영하세요.
JSON만 출력하세요. 다른 텍스트 없이.

{
  "invention_title": "발명 명칭 또는 null",
  "technical_field": "기술 분야 또는 null",
  "problem": "해결 문제 또는 null",
  "solution": "핵심 해결 수단 또는 null",
  "key_components": ["구성요소1", "구성요소2"] 또는 [],
  "process_steps": ["단계1", "단계2"] 또는 [],
  "effect": "발명 효과 또는 null",
  "keywords": ["키워드1", "키워드2"] 또는 []
}"""


def extract_invention(conversation: list) -> dict:
    """대화 전체를 보고 invention.json 초안 생성/업데이트"""
    messages = [{"role": "system", "content": EXTRACT_SYSTEM}]
    messages += conversation

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        temperature=0.1,
        messages=messages
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()

    try:
        extracted = json.loads(raw)
        # 스키마 기본값으로 병합
        result = dict(INVENTION_SCHEMA)
        result.update({k: v for k, v in extracted.items() if v is not None and v != []})
        return result
    except json.JSONDecodeError:
        return dict(INVENTION_SCHEMA)


# ──────────────────────────────────────────
# 질문 생성
# ──────────────────────────────────────────

def generate_questions(missing_fields: list) -> str:
    """missing_fields 기반으로 자연스러운 질문 생성 (최대 2개)"""
    target = missing_fields[:2]  # 한 번에 최대 2개
    questions = []
    for i, field in enumerate(target, 1):
        questions.append(f"{i}. {QUESTIONS[field]}")
    return "\n".join(questions)


# ──────────────────────────────────────────
# 메인 대화 루프
# ──────────────────────────────────────────

def run_consultation():
    """상담 에이전트 메인 실행"""

    session_id = str(uuid.uuid4())[:8]
    conversation = []  # {"role": "user"/"assistant", "content": "..."}
    invention = dict(INVENTION_SCHEMA)

    print("=" * 60)
    print("특허 상담 에이전트")
    print("발명 내용을 자유롭게 설명해주세요.")
    print("종료하려면 'q' 입력")
    print("=" * 60)

    # 1턴: 첫 발화 받기
    first_input = input("\n사용자: ").strip()
    if first_input.lower() == 'q':
        return

    conversation.append({"role": "user", "content": first_input})

    MAX_TURNS = 4  # 최대 4턴 (첫 발화 + 보완 3회)

    for turn in range(MAX_TURNS):
        print("\n  [분석 중...]")

        # invention.json 업데이트
        invention = extract_invention(conversation)
        score = calc_score(invention)
        missing = get_missing_fields(invention)

        print(f"  완성도: {score:.0%} | 부족 필드: {missing}")

        # 완성도 충분하면 종료
        if score >= 0.7 or not missing:
            print("\n  충분한 정보가 수집되었습니다. ✅")
            break

        # 마지막 턴이면 종료
        if turn == MAX_TURNS - 1:
            print("\n  최대 대화 횟수에 도달했습니다.")
            break

        # 부족 필드 질문
        questions = generate_questions(missing)
        reply = f"감사합니다! 조금 더 구체적으로 여쭤볼게요.\n\n{questions}"
        print(f"\n에이전트: {reply}")

        conversation.append({"role": "assistant", "content": reply})

        user_input = input("\n사용자: ").strip()
        if user_input.lower() == 'q':
            break

        conversation.append({"role": "user", "content": user_input})

    # 최종 invention.json 저장
    save_result(invention, session_id, conversation)


# ──────────────────────────────────────────
# 저장 (3.12 포맷)
# ──────────────────────────────────────────

def save_result(invention: dict, session_id: str, conversation: list):
    """invention.json 최종 저장"""

    os.makedirs("inventions", exist_ok=True)

    # 메타 정보 추가
    invention["_meta"] = {
        "session_id": session_id,
        "created_at": datetime.datetime.now().isoformat(),
        "turns": len([m for m in conversation if m["role"] == "user"]),
        "model": MODEL,
        "completeness_score": calc_score(invention),
        "missing_fields": get_missing_fields(invention)
    }

    output_path = f"inventions/invention_{session_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(invention, f, ensure_ascii=False, indent=2)

    # 대화 로그 저장 (추적용)
    log_path = f"inventions/log_{session_id}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(conversation, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"invention.json 저장 완료: {output_path}")
    print(f"대화 로그 저장 완료:      {log_path}")
    print(f"완성도: {invention['_meta']['completeness_score']:.0%}")

    print("\n=== 최종 invention.json ===")
    display = {k: v for k, v in invention.items() if k != "_meta"}
    print(json.dumps(display, ensure_ascii=False, indent=2))

    print("\n=== 선행기술조사 에이전트에 전달할 핵심 필드 ===")
    handoff = {
        "keywords": invention.get("keywords", []),
        "technical_field": invention.get("technical_field"),
        "problem": invention.get("problem"),
        "solution": invention.get("solution"),
    }
    print(json.dumps(handoff, ensure_ascii=False, indent=2))


# ──────────────────────────────────────────
# 테스트 모드 (자동 입력)
# ──────────────────────────────────────────

def test_mode():
    """자동 입력으로 빠른 동작 확인"""

    print("=" * 60)
    print("상담 에이전트 테스트 모드")
    print("=" * 60)

    # 시나리오: 냉장고 원격 제어 앱
    test_conversation = [
        {
            "role": "user",
            "content": "스마트폰으로 집에 있는 냉장고 온도를 원격으로 조절하고 음식 유통기한을 알려주는 앱을 만들었어요."
        },
        {
            "role": "assistant",
            "content": "감사합니다! 조금 더 여쭤볼게요.\n1. 기존에 어떤 불편함이 있어서 이 발명을 하게 되셨나요?\n2. 발명을 구성하는 주요 부품이나 기능 요소가 무엇인가요?"
        },
        {
            "role": "user",
            "content": "기존엔 냉장고 상태를 확인하려면 직접 가야 했고, 음식이 언제 상하는지 몰라서 낭비가 심했어요. 스마트폰 앱, 냉장고 내부 카메라, IoT 센서, 서버로 구성돼요."
        }
    ]

    print("\n[테스트 대화 시뮬레이션]")
    for msg in test_conversation:
        role = "사용자" if msg["role"] == "user" else "에이전트"
        print(f"\n{role}: {msg['content'][:100]}...")

    print("\n  [invention.json 생성 중...]")
    invention = extract_invention(test_conversation)
    score = calc_score(invention)
    missing = get_missing_fields(invention)

    print(f"\n완성도: {score:.0%}")
    print(f"부족 필드: {missing}")
    print("\n=== 생성된 invention.json ===")
    print(json.dumps(invention, ensure_ascii=False, indent=2))

    # 저장
    save_result(invention, "TEST-001", test_conversation)


# ──────────────────────────────────────────
# 메인
# ──────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # python consultation_agent.py test
        test_mode()
    else:
        # python consultation_agent.py
        run_consultation()
