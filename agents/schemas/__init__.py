"""Agent output schemas for the patent MVP pipeline."""
from agents.schemas.common import AgentOutputBase, AgentOutputStatus, EvidenceItem
from agents.schemas.consultation import ConsultationAgentOutput, FollowupQuestion, InventionComponent
from agents.schemas.claim import ClaimAgentOutput, ClaimDraft
from agents.schemas.drawing import DrawingAgentOutput, FigureDraft, ReferenceNumeral
from agents.schemas.prior_art import PriorArtAgentOutput, PriorArtCandidate
from agents.schemas.specification import SpecificationAgentOutput
from agents.schemas.composer import ComposerAgentOutput

__all__ = [
    "AgentOutputBase",
    "AgentOutputStatus",
    "EvidenceItem",
    "ConsultationAgentOutput",
    "FollowupQuestion",
    "InventionComponent",
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
