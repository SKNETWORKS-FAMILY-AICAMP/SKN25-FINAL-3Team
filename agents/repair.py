"""LLM 기반 agent output schema repair.

Repair는 review가 아니다. raw_output의 특허 내용을 새로 쓰거나 품질을 개선하지 않고,
Pydantic schema에 맞게 필드명/타입/리스트 구조만 정규화한다.
"""
from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_REPAIR_MODEL = os.getenv("AGENT_REPAIR_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
MAX_RAW_OUTPUT_CHARS = int(os.getenv("AGENT_REPAIR_MAX_RAW_CHARS", "12000"))

PIPELINE_CONTEXT = "입력 → 상담 → 청구항 → 도면/선행기술/명세서 → Composer → 최종 출력"

AGENT_REPAIR_HINTS: dict[str, str] = {
    "consultation": "문제, 해결수단, 구성요소, 입력 데이터, 출력 결과, 효과, 부족정보, 추가질문을 raw_output에서 보존한다.",
    "claim": "청구항 번호, 독립/종속, method/system/storage_medium 분류, depends_on, 청구항 문장, 구성요소를 보존한다. 새 청구항을 작성하지 않는다.",
    "drawing": "도면 번호, 도면 제목/유형, 구성요소, 설명, 참조부호를 보존한다. 새 도면을 만들지 않는다.",
    "prior_art": "검색 query, 후보 patent_id/title/score, 겹치는 점, 차이점, 근거, PDF 경로를 보존한다. 후보 특허를 상상하지 않는다.",
    "specification": "기술분야/배경기술/과제/해결수단/효과/도면설명/상세설명 섹션 텍스트를 보존한다. 새 명세서 내용을 쓰지 않는다.",
    "composer": "최종 markdown/html/section 구조를 보존한다. 누락된 특허 내용을 새로 만들지 않는다.",
}


def _safe_json(value: Any, *, max_chars: int | None = None) -> str:
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
    """Repair LLM에 넘길 단일 prompt를 만든다."""

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
    """OpenAI API로 raw output을 schema-conforming JSON으로 1회 repair한다.

    OPENAI_API_KEY가 없거나 openai 패키지가 없으면 예외를 던진다. 호출 여부와 fallback은
    agents.validation.safe_validate_output()에서 제어한다.
    """

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set; cannot run LLM repair")

    from openai import OpenAI  # optional dependency: repair를 실제 호출할 때만 필요

    prompt = build_repair_prompt(
        agent_name=agent_name,
        schema_name=schema_name,
        schema_json=schema_json,
        raw_output=raw_output,
        validation_errors=validation_errors,
    )
    client = OpenAI()
    response = client.chat.completions.create(
        model=model or DEFAULT_REPAIR_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You repair invalid agent JSON into schema-conforming JSON. Return JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
