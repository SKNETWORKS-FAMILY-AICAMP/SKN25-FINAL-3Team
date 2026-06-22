"""도면 agent output schema."""
from __future__ import annotations

from pydantic import BaseModel, Field

from agents.schemas.common import AgentOutputBase


class FigureDraft(BaseModel):
    fig_no: str
    title: str = ""
    type: str = ""
    components: list[str] = Field(default_factory=list)
    description: str = ""


class ReferenceNumeral(BaseModel):
    number: str
    label: str
    description: str = ""
    component_id: str | None = None


class DrawingAgentOutput(AgentOutputBase):
    figures: list[FigureDraft] = Field(default_factory=list)
    reference_numerals: list[ReferenceNumeral] = Field(default_factory=list)
    drawing_notes: list[str] = Field(default_factory=list)
