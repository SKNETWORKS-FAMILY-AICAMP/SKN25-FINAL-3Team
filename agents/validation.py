"""Agent output validation utilities.

─ 검증 흐름 ─
  1. normalize_to_schema_shape() : 흔한 LLM 형식 오류 교정 (list/str 등)
  2. schema.model_validate()     : Pydantic 검증
  3. 실패 시 LLM repair 1회 시도  (ENABLE_LLM_REPAIR=true 일 때만)
  4. repair도 실패하면 AgentValidationError 발생 → 파이프라인 중단

─ 이전 방식과의 차이 ─
  이전: 검증 실패 → 조용히 fallback 반환 → 파이프라인 계속 (silent failure)
  현재: 검증 실패 → 예외 발생 → 파이프라인 명시적 중단

  특허 문서처럼 내용의 정확성이 중요한 서비스에서는
  빈 결과물로 계속 진행하는 것보다 실패를 명확히 드러내는 게 낫습니다.
  실패한 agent는 /api/agents/{agent_name}/run 으로 개별 재실행할 수 있습니다.
"""
from __future__ import annotations

import os
from types import UnionType
from typing import Any, Callable, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError

from agents.repair import repair_agent_output_with_llm

OutputModelT = TypeVar("OutputModelT", bound=BaseModel)
RepairFn = Callable[..., dict[str, Any]]


class AgentValidationError(Exception):
    """Agent output이 Pydantic schema 검증을 통과하지 못했을 때 발생합니다.

    graph.py의 try/except가 이 예외를 잡아서 state["workflow"]["errors"]에 기록하고
    파이프라인을 중단합니다.
    실패한 agent는 /api/agents/{agent_name}/run 으로 개별 재실행할 수 있습니다.
    """

    def __init__(
        self,
        agent_name: str,
        schema_name: str,
        validation_errors: list[dict[str, Any]],
        raw_output: Any,
        repair_error: str | None = None,
    ) -> None:
        self.agent_name = agent_name
        self.schema_name = schema_name
        self.validation_errors = validation_errors
        self.raw_output = raw_output
        self.repair_error = repair_error

        msg = f"[{agent_name}] {schema_name} 검증 실패"
        if repair_error:
            msg += f" / repair도 실패: {repair_error}"
        msg += f" / 재실행: POST /api/agents/{agent_name}/run"
        super().__init__(msg)


def _unwrap_optional(annotation: Any) -> Any:
    """Optional[X] 또는 X | None 타입에서 실제 타입 X를 꺼냅니다."""
    origin = get_origin(annotation)
    if origin in {UnionType, Union}:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        return args[0] if len(args) == 1 else annotation
    return annotation


def _first_string_field(model: type[BaseModel]) -> str | None:
    """Pydantic 모델에서 첫 번째 문자열 필드의 이름을 찾습니다."""
    preferred = ("name", "title", "canonical_name", "effect", "summary", "description", "text")
    for candidate in preferred:
        field = model.model_fields.get(candidate)
        if field is not None and _unwrap_optional(field.annotation) is str:
            return candidate
    for name, field in model.model_fields.items():
        ann = _unwrap_optional(field.annotation)
        if ann is str and field.is_required():
            return name
    for name, field in model.model_fields.items():
        ann = _unwrap_optional(field.annotation)
        if ann is str:
            return name
    return None


def _fill_common_missing_model_fields(value: dict[str, Any], model: type[BaseModel], index: int) -> dict[str, Any]:
    """schema에서 유추 가능한 메타데이터 필드만 채웁니다. 발명 내용은 만들지 않습니다."""
    filled = dict(value)
    for name, field in model.model_fields.items():
        ann = _unwrap_optional(field.annotation)
        if name in filled:
            continue
        if name == "order" and ann is int:
            filled[name] = index
        elif get_origin(ann) is list:
            filled[name] = []
    return filled


def normalize_to_schema_shape(raw: Any, schema: type[BaseModel]) -> Any:
    """Pydantic 검증 전에 흔한 LLM JSON 형식 오류를 자동으로 교정합니다.

    내용을 새로 만들거나 바꾸지 않고 형식(shape)만 조정합니다.
    - list[str] 필드에 문자열 1개 → [문자열]로 감싸줌
    - str 필드에 None → 빈 문자열
    - str 필드에 list → ", ".join()
    """
    if isinstance(raw, BaseModel):
        return raw
    if not isinstance(raw, dict):
        return raw

    normalized = dict(raw)

    for field_name, field in schema.model_fields.items():
        if field_name not in normalized:
            continue

        value = normalized[field_name]
        annotation = _unwrap_optional(field.annotation)
        origin = get_origin(annotation)
        args = get_args(annotation)

        if annotation is str:
            if value is None:
                normalized[field_name] = ""
            elif isinstance(value, list):
                normalized[field_name] = ", ".join(str(item) for item in value)
            elif isinstance(value, dict):
                normalized[field_name] = "; ".join(f"{k}: {v}" for k, v in value.items())
            continue

        if origin is list and args:
            item_type = _unwrap_optional(args[0])
            if value is None:
                normalized[field_name] = []
                continue
            if isinstance(value, str):
                value = [value] if value else []
            if isinstance(value, list):
                items = []
                for idx, item in enumerate(value, 1):
                    if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                        if isinstance(item, str):
                            target = _first_string_field(item_type)
                            if target is not None:
                                item = {target: item}
                            # target이 None이면 item을 그대로 두어 Pydantic이 의미 있는 에러를 냅니다.
                        if isinstance(item, dict):
                            item = _fill_common_missing_model_fields(item, item_type, idx)
                            item = normalize_to_schema_shape(item, item_type)
                    items.append(item)
                normalized[field_name] = items
            continue

        if isinstance(annotation, type) and issubclass(annotation, BaseModel) and isinstance(value, dict):
            normalized[field_name] = normalize_to_schema_shape(value, annotation)

    return normalized


def safe_validate_output(
    *,
    agent_name: str,
    schema: type[OutputModelT],
    raw_output: Any,
    repair_fn: RepairFn | None = repair_agent_output_with_llm,
    enable_llm_repair: bool | None = None,
) -> OutputModelT:
    """Agent raw output을 schema 모델로 변환합니다. 실패 시 AgentValidationError를 발생시킵니다.

    흐름:
    1. normalize_to_schema_shape() 로 형식 교정
    2. schema.model_validate() 로 Pydantic 검증
    3. 실패 시 → repair 시도 (ENABLE_LLM_REPAIR=true 일 때만)
    4. repair 실패 또는 repair 꺼져있으면 → AgentValidationError 발생

    Args:
        agent_name: 로그/에러 메시지에 쓸 agent 이름
        schema: 검증에 쓸 Pydantic 모델 클래스
        raw_output: agent가 반환한 원본 데이터
        repair_fn: LLM repair 함수. None이면 repair 건너뜀.
        enable_llm_repair: None이면 환경변수 ENABLE_LLM_REPAIR로 결정.
                           기본값 false: 의도치 않은 OpenAI 비용 방지.
                           켜려면 .env에 ENABLE_LLM_REPAIR=true 설정.
    """
    # 1단계: 형식 교정 후 Pydantic 검증
    normalized_raw = normalize_to_schema_shape(raw_output, schema)
    try:
        return schema.model_validate(normalized_raw)
    except ValidationError as first_error:
        first_errors = first_error.errors()

    # LLM repair 사용 여부 결정
    # 기본값 false: OPENAI_API_KEY 없거나 다른 LLM 환경에서 의도치 않은 비용 방지
    if enable_llm_repair is None:
        enable_llm_repair = os.getenv("ENABLE_LLM_REPAIR", "false").lower() in {"1", "true", "yes", "on"}

    # 2단계: LLM repair 시도 (켜져있을 때만)
    repair_error: str | None = None
    if enable_llm_repair and repair_fn is not None:
        try:
            repaired_raw = repair_fn(
                agent_name=agent_name,
                schema_name=schema.__name__,
                schema_json=schema.model_json_schema(),
                raw_output=normalized_raw,
                validation_errors=first_errors,
            )
            return schema.model_validate(repaired_raw)
        except Exception as exc:  # noqa: BLE001
            repair_error = repr(exc)

    # 3단계: 모든 시도 실패 → 예외 발생
    # 호출 측(graph.py)이 이 예외를 잡아서 파이프라인을 명시적으로 중단합니다.
    raise AgentValidationError(
        agent_name=agent_name,
        schema_name=schema.__name__,
        validation_errors=first_errors,
        raw_output=raw_output,
        repair_error=repair_error,
    )
