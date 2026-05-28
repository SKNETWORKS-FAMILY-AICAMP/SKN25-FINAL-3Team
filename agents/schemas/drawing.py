"""도면 agent output schema."""
from __future__ import annotations

from pydantic import BaseModel, Field

from agents.schemas.common import AgentOutputBase


class FigureDraft(BaseModel):
    fig_no: int | str
    title: str = ""
    type: str = ""
    purpose: str = ""
    components: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    description: str = ""


class ReferenceNumeral(BaseModel):
    number: str
    term: str
    figure: str = ""
    component_id: str = ""
    description: str = ""


class DrawingAgentOutput(AgentOutputBase):
    figures: list[FigureDraft] = Field(default_factory=list)
    reference_numerals: dict[str, ReferenceNumeral] = Field(default_factory=dict)
    drawing_notes: list[str] = Field(default_factory=list)
