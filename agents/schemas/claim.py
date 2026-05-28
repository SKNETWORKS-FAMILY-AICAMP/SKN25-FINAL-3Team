"""청구항 agent output schema."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from agents.schemas.common import AgentOutputBase

ClaimType = Literal["independent", "dependent"]
ClaimCategory = Literal["method", "system", "storage_medium", "unknown"]


class ClaimDraft(BaseModel):
    claim_no: int
    type: ClaimType = "independent"
    category: ClaimCategory = "method"
    depends_on: list[int] = Field(default_factory=list)
    elements: list[str] = Field(default_factory=list)
    text: str
    source_components: list[str] = Field(default_factory=list)
    review_flags: list[str] = Field(default_factory=list)


class ClaimAgentOutput(AgentOutputBase):
    claim_plan: dict[str, Any] = Field(default_factory=dict)
    draft_claims: list[ClaimDraft] = Field(default_factory=list)
    independent_claim_numbers: list[int] = Field(default_factory=list)
    dependent_claim_numbers: list[int] = Field(default_factory=list)
    claim_strategy_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_claims(self) -> "ClaimAgentOutput":
        nums = [claim.claim_no for claim in self.draft_claims]
        if len(nums) != len(set(nums)):
            raise ValueError("claim_no must be unique")
        for claim in self.draft_claims:
            if not claim.text.strip():
                raise ValueError(f"claim {claim.claim_no} text is empty")
            if claim.type == "dependent" and not claim.depends_on:
                raise ValueError(f"dependent claim {claim.claim_no} requires depends_on")
        return self
