"""발명의 설명 agent output schema."""
from __future__ import annotations

from agents.schemas.common import AgentOutputBase


class SpecificationAgentOutput(AgentOutputBase):
    technical_field: str = ""
    background_art: str = ""
    problem_to_solve: str = ""
    means_for_solving: str = ""
    effects: str = ""
    brief_description_of_drawings: str = ""
    detailed_description: str = ""
