"""Agent output schemas for the patent MVP pipeline."""
from agents.schemas.common import AgentOutputBase, AgentOutputStatus, EvidenceItem
from agents.schemas.master import MasterAction, MasterAgentOutput, MasterStage
from agents.schemas.summary import (
    InventorInput,
    StructuredInvention,
    SummaryAgentOutput,
    SummaryComponent,
    SummaryProcessStep,
)
from agents.schemas.claim import ClaimAgentOutput, ClaimDraft
from agents.schemas.drawing import DrawingAgentOutput, FigureDraft, ReferenceNumeral
from agents.schemas.prior_art import PriorArtAgentOutput, PriorArtCandidate
from agents.schemas.specification import SpecificationAgentOutput
from agents.schemas.composer import ComposerAgentOutput

__all__ = [
    "AgentOutputBase",
    "AgentOutputStatus",
    "EvidenceItem",
    "MasterAction",
    "MasterAgentOutput",
    "MasterStage",
    "InventorInput",
    "StructuredInvention",
    "SummaryAgentOutput",
    "SummaryComponent",
    "SummaryProcessStep",
    "ClaimAgentOutput",
    "ClaimDraft",
    "DrawingAgentOutput",
    "FigureDraft",
    "ReferenceNumeral",
    "PriorArtAgentOutput",
    "PriorArtCandidate",
    "SpecificationAgentOutput",
    "ComposerAgentOutput",
]
