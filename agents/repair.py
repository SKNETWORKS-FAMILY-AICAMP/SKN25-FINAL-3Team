"""LLM 기반 agent output schema repair.

─ repair의 목적 ─
  agent가 반환한 JSON이 Pydantic schema와 형식이 맞지 않을 때,
  GPT에게 "내용은 그대로 두고 형식(필드명/타입/구조)만 고쳐달라"고 요청합니다.
  새 특허 내용을 만들거나 품질을 개선하는 게 아니라, 형식 정규화만 합니다.

─ 언제 호출되는가? ─
  agents/validation.py의 safe_validate_output()에서
  Pydantic 검증이 실패했을 때 1회만 호출됩니다.
  repair도 실패하면 AgentValidationError로 중단됩니다.
"""
from __future__ import annotations

import json
import os
from typing import Any

# repair에 쓸 GPT 모델. 환경변수로 바꿀 수 있습니다.
# 기본값은 gpt-4o-mini (빠르고 저렴함. repair는 형식 교정만이라 고성능 모델 불필요).
DEFAULT_REPAIR_MODEL = os.getenv("AGENT_REPAIR_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

# repair에 넘기는 raw_output이 너무 길면 토큰 초과가 납니다.
# 이 글자 수를 넘으면 잘라서 보냅니다.
MAX_RAW_OUTPUT_CHARS = int(os.getenv("AGENT_REPAIR_MAX_RAW_CHARS", "12000"))

# GPT에게 파이프라인 전체 맥락을 설명하는 문장 (repair 프롬프트에 포함)
PIPELINE_CONTEXT = "입력 → 요약본작성 → 청구항 → 도면/선행기술/명세서 → Composer → 최종 출력"

# 각 agent별로 repair 시 특별히 신경 써야 할 내용 (프롬프트에 포함)
AGENT_REPAIR_HINTS: dict[str, str] = {
    "master": "현재 단계, 다음 action, current_agent, next_agent, pipeline_index, 요약본 승인 여부를 보존한다.",
    "summary": "5개 입력 필드, readable_summary, structured_invention, feedback_applied, warnings를 raw_output에서 보존한다.",
    "claim": "청구항 번호, 독립/종속, method/system/storage_medium 분류, depends_on, 청구항 문장, 구성요소를 보존한다. 새 청구항을 작성하지 않는다.",
    "drawing": "도면 번호, 도면 제목/유형, 구성요소, 설명, 참조부호를 보존한다. 새 도면을 만들지 않는다.",
    "prior_art": "검색 query, 후보 patent_id/title/score, 겹치는 점, 차이점, 근거, PDF 경로를 보존한다. 후보 특허를 상상하지 않는다.",
    "specification": "기술분야/배경기술/과제/해결수단/효과/도면설명/상세설명 섹션 텍스트를 보존한다. 새 명세서 내용을 쓰지 않는다.",
    "composer": "최종 markdown/html/section 구조를 보존한다. 누락된 특허 내용을 새로 만들지 않는다.",
}


def _safe_json(value: Any, *, max_chars: int | None = None) -> str:
    """Python 객체를 JSON 문자열로 변환합니다. max_chars를 넘으면 뒷부분을 자릅니다."""
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n...<truncated>"
    return text


def build_repair_prompt(
    *,
    agent_name: str,
    schema_name: str,
    schema_json: dict[str, Any],
    raw_output: Any,
    validation_errors: list[dict[str, Any]],
) -> str:
    """GPT에게 보낼 repair 프롬프트를 만듭니다.

    프롬프트에 포함되는 내용:
    - 이 output이 어느 agent의 결과인지
    - 어떤 schema에 맞춰야 하는지 (JSON Schema 형식)
    - Pydantic이 발견한 검증 오류 목록
    - 원본 raw_output
    - 주의사항 (내용을 새로 만들지 말 것)
    """
    hint = AGENT_REPAIR_HINTS.get(agent_name, "raw_output의 유용한 내용을 schema 필드에 맞게 보존한다.")
    return f"""너는 특허 멀티에이전트 파이프라인의 output schema repair 함수다.

파이프라인:
{PIPELINE_CONTEXT}

이 output은 {agent_name} agent 결과다.
최종적으로 {schema_name} schema에 맞아야 한다.
raw_output 안에 있는 내용을 버리지 말고 필드에 맞게 옮겨라.
없는 내용은 만들지 말고 빈 값으로 둬라.
품질 개선이나 새 특허 내용 생성은 하지 마라.
JSON object 하나만 반환하고 설명/Markdown/code block은 출력하지 마라.

agent별 보존 기준:
{hint}

Pydantic JSON Schema:
{_safe_json(schema_json)}

Validation errors:
{_safe_json(validation_errors)}

Raw output:
{_safe_json(raw_output, max_chars=MAX_RAW_OUTPUT_CHARS)}
"""


def repair_agent_output_with_llm(
    *,
    agent_name: str,
    schema_name: str,
    schema_json: dict[str, Any],
    raw_output: Any,
    validation_errors: list[dict[str, Any]],
    model: str | None = None,
) -> dict[str, Any]:
    """OpenAI API로 raw output을 schema-conforming JSON으로 1회 repair합니다.

    이 함수는 safe_validate_output()에서만 호출됩니다.
    직접 호출하지 마세요.

    실패 조건 (예외 발생):
    - OPENAI_API_KEY 환경변수가 없을 때
    - openai 패키지가 설치 안 됐을 때
    - API 호출 자체가 실패했을 때
    - GPT가 반환한 JSON이 파싱 불가할 때

    예외가 발생하면 safe_validate_output()이 받아서 AgentValidationError로 중단합니다.
    """
    # OPENAI_API_KEY는 .env 파일에 넣어두세요.
    # Docker에서는 compose.service.yml의 env_file로 자동 로드됩니다.
    # 로컬 실행 시에는 main.py의 load_dotenv()가 처리합니다.
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set; cannot run LLM repair")

    # openai 패키지는 repair를 실제 호출할 때만 import합니다.
    # repair를 안 쓰는 환경에서 openai가 설치 안 돼있어도 에러가 안 납니다.
    from openai import OpenAI

    prompt = build_repair_prompt(
        agent_name=agent_name,
        schema_name=schema_name,
        schema_json=schema_json,
        raw_output=raw_output,
        validation_errors=validation_errors,
    )

    client = OpenAI()  # OPENAI_API_KEY 환경변수를 자동으로 읽습니다
    response = client.chat.completions.create(
        model=model or DEFAULT_REPAIR_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You repair invalid agent JSON into schema-conforming JSON. Return JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,                              # 창의성 0: 정해진 형식에 맞게만 고칩니다
        response_format={"type": "json_object"},    # GPT가 반드시 JSON만 반환하도록 강제
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
