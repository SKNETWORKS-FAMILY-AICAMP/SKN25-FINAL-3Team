"""공통 Pydantic output schema.

LangGraph shared state는 TypedDict/dict로 유지하고, 이 모델들은 각 agent의
raw output을 state에 넣기 전 검증하는 최소 계약으로 사용한다.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

AgentOutputStatus = Literal["ok", "needs_user_input", "failed"]


class EvidenceItem(BaseModel):
    """검증/보고서에 남길 짧은 근거 조각."""

    source: str = ""
    text: str = ""
    path: str | None = None
    score: float | None = None


class AgentOutputBase(BaseModel):
    """모든 agent output이 공유하는 최소 메타 필드."""

    model_config = ConfigDict(extra="allow")

    status: AgentOutputStatus = "ok"
    summary: str = ""
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
