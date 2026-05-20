"""선행기술 agent output schema."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from agents.schemas.common import AgentOutputBase


class PriorArtCandidate(BaseModel):
    patent_id: str
    title: str = ""
    score: float = 0.0
    matched_points: list[str] = Field(default_factory=list)
    difference_points: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    pdf_path: str | None = None

    @field_validator("score")
    @classmethod
    def clamp_score(cls, value: float) -> float:
        # retrieval score는 법적 확신도가 아니므로 데모 표시용 0~1 범위로 정규화한다.
        return max(0.0, min(1.0, float(value)))


class PriorArtAgentOutput(AgentOutputBase):
    query: str = ""
    candidates: list[PriorArtCandidate] = Field(default_factory=list)
    overlap_points: list[str] = Field(default_factory=list)
    difference_points: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
