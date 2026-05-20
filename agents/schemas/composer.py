"""Composer/최종 패키징 agent output schema."""
from __future__ import annotations

from pydantic import Field, model_validator

from agents.schemas.common import AgentOutputBase


class ComposerAgentOutput(AgentOutputBase):
    title: str = ""
    abstract: str = ""
    sections: dict[str, str] = Field(default_factory=dict)
    rendered_markdown: str = ""
    rendered_html_path: str | None = None
    unresolved_items: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_renderable_output(self) -> "ComposerAgentOutput":
        if self.status == "ok" and not (self.rendered_markdown.strip() or self.sections):
            raise ValueError("composer output needs rendered_markdown or sections")
        return self
