"""Agent output validation utilities.

흐름: Pydantic validate → 실패 시 LLM repair 1회 → 재검증 → 실패 시 hard fallback.
"""
from __future__ import annotations

import os
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ValidationError

from agents.repair import repair_agent_output_with_llm

OutputModelT = TypeVar("OutputModelT", bound=BaseModel)
RepairFn = Callable[..., dict[str, Any]]


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

    try:
        return schema.model_validate(raw_output)
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
                raw_output=raw_output,
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
        fallback.details["validation"]["repaired_raw_output"] = repaired_raw
        fallback.details["validation"]["repair_error"] = repair_error
    return fallback
