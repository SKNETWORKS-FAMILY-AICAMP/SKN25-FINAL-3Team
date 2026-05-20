"""상담/요약 agent output schema."""
from __future__ import annotations

from pydantic import BaseModel, Field

from agents.schemas.common import AgentOutputBase


class InventionComponent(BaseModel):
    id: str = ""
    name: str
    role: str = ""
    evidence: str | None = None


class FollowupQuestion(BaseModel):
    question: str
    target_slot: str = ""
    why_needed: str = ""
    expected_answer_type: str | None = None


class ConsultationAgentOutput(AgentOutputBase):
    invention_title: str = ""
    problem: str = ""
    solution: str = ""
    components: list[InventionComponent] = Field(default_factory=list)
    input_data: list[str] = Field(default_factory=list)
    output_result: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)
    missing_slots: list[str] = Field(default_factory=list)
    followup_questions: list[FollowupQuestion] = Field(default_factory=list)
