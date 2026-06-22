"""Agent output validation utilities.

흐름: Pydantic validate → 실패 시 LLM repair 1회 → 재검증 → 실패 시 hard fallback.
"""
from __future__ import annotations

import os
from types import UnionType
from typing import Any, Callable, TypeVar, get_args, get_origin

from pydantic import BaseModel, ValidationError

from agents.repair import repair_agent_output_with_llm

OutputModelT = TypeVar("OutputModelT", bound=BaseModel)
RepairFn = Callable[..., dict[str, Any]]


def _unwrap_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin in {UnionType, getattr(__import__("typing"), "Union")}:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        return args[0] if len(args) == 1 else annotation
    return annotation


def _first_string_field(model: type[BaseModel]) -> str | None:
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
    """Fill schema-obvious metadata only; never invent domain content."""
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
    """Generic, schema-driven shape normalization before Pydantic validation.

    목적은 내용 보정이 아니라 흔한 LLM JSON shape drift만 흡수하는 것이다.
    예: list[str] 필드에 문자열 1개가 온 경우 → [문자열],
        list[SubModel] 필드에 문자열 항목이 온 경우 → SubModel의 첫 str 필드에 매핑.
    특정 agent/domain 키워드를 보지 않고 Pydantic schema annotation만 사용한다.
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
                            item = {target: item} if target else {}
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
    fallback: OutputModelT,
    repair_fn: RepairFn | None = repair_agent_output_with_llm,
    enable_llm_repair: bool | None = None,
) -> OutputModelT:
    """Agent raw output을 안전하게 schema 모델로 변환한다.

    - 1차: schema.model_validate(raw_output)
    - 실패: repair_fn으로 LLM repair 1회 시도
    - repair 결과 재검증
    - 여전히 실패하거나 repair 호출 불가: hard fallback 반환
    """

    normalized_raw = normalize_to_schema_shape(raw_output, schema)
    try:
        return schema.model_validate(normalized_raw)
    except ValidationError as first_error:
        first_errors = first_error.errors()

    if enable_llm_repair is None:
        enable_llm_repair = os.getenv("ENABLE_LLM_REPAIR", "true").lower() in {"1", "true", "yes", "on"}

    repaired_raw: Any = None
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
            repaired = schema.model_validate(repaired_raw)
            if hasattr(repaired, "warnings"):
                repaired.warnings.append(f"{agent_name} output validation failed once; LLM repair used")
            if hasattr(repaired, "details"):
                repaired.details.setdefault("validation", {})["first_errors"] = first_errors
                repaired.details["validation"]["repaired"] = True
            return repaired
        except Exception as exc:  # noqa: BLE001 - repair 실패는 hard fallback으로 흡수한다.
            repair_error = repr(exc)

    if hasattr(fallback, "warnings"):
        fallback.warnings.append(
            f"{agent_name} output validation failed; hard fallback used"
        )
        if repair_error:
            fallback.warnings.append(f"LLM repair failed or unavailable: {repair_error}")
    if hasattr(fallback, "details"):
        fallback.details.setdefault("validation", {})["first_errors"] = first_errors
        fallback.details["validation"]["raw_output"] = raw_output
        fallback.details["validation"]["normalized_raw_output"] = normalized_raw
        fallback.details["validation"]["repaired_raw_output"] = repaired_raw
        fallback.details["validation"]["repair_error"] = repair_error
    return fallback
