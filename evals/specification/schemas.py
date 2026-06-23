"""Pydantic contracts for specification evaluation cases and reports."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TechnologyProfile = Literal["general", "ai_software", "bio_pharma", "parameter"]
Severity = Literal["info", "minor", "major", "critical"]
Attribution = Literal["agent", "input", "mixed"]


class SkilledPersonProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    experience: str
    common_general_knowledge: list[str] = Field(default_factory=list)


class CaseExpectations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    must_cover: list[str] = Field(default_factory=list)
    must_not_invent: list[str] = Field(default_factory=list)


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    description: str = ""
    filing_date: str
    technology_profile: TechnologyProfile = "general"
    skilled_person: SkilledPersonProfile
    agent_state: dict[str, Any]
    expected: CaseExpectations = Field(default_factory=CaseExpectations)


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Severity
    category: str
    description: str
    attribution: Attribution = "mixed"
    source_path: str | None = None
    spec_section: str | None = None
    quote: str | None = None
    experimentation_class: Literal[
        "not_applicable",
        "routine_knowledge",
        "minor_experiment",
        "special_knowledge_required",
        "undue_experimentation",
        "unknown",
    ] = "not_applicable"


class SubcriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subcriterion_id: str
    score: int = Field(ge=0)
    max_score: int = Field(gt=0)
    reason: str


class CriterionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: str
    score: int = Field(ge=0)
    max_score: int = Field(gt=0)
    subcriteria: list[SubcriterionScore]
    findings: list[Finding] = Field(default_factory=list)
    reason: str


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criteria: list[CriterionResult]
    critical_failures: list[Finding] = Field(default_factory=list)
    input_gaps: list[Finding] = Field(default_factory=list)
    agent_issues: list[Finding] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    summary: str

    @model_validator(mode="before")
    @classmethod
    def fill_contextual_attribution(cls, value: Any) -> Any:
        """Recover safely when the Judge omits attribution on a finding."""
        if not isinstance(value, dict):
            return value

        normalized = dict(value)

        def normalize_findings(items: Any, default: Attribution) -> Any:
            if not isinstance(items, list):
                return items
            output = []
            for item in items:
                if isinstance(item, dict):
                    item = dict(item)
                    item.setdefault("attribution", default)
                output.append(item)
            return output

        normalized["critical_failures"] = normalize_findings(
            normalized.get("critical_failures", []),
            "mixed",
        )
        normalized["input_gaps"] = normalize_findings(
            normalized.get("input_gaps", []),
            "input",
        )
        normalized["agent_issues"] = normalize_findings(
            normalized.get("agent_issues", []),
            "agent",
        )

        criteria = normalized.get("criteria")
        if isinstance(criteria, list):
            normalized_criteria = []
            for criterion in criteria:
                if isinstance(criterion, dict):
                    criterion = dict(criterion)
                    criterion["findings"] = normalize_findings(
                        criterion.get("findings", []),
                        "mixed",
                    )
                normalized_criteria.append(criterion)
            normalized["criteria"] = normalized_criteria

        return normalized


class MechanicalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    critical_failures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    rubric_version: str
    generated_at: str
    candidate_source: str
    generator_model: str
    judge_model: str
    total_score: int
    grade: Literal["A", "B", "C", "D"]
    passed: bool
    decision_reasons: list[str]
    mechanical: MechanicalResult
    judge: JudgeResult
    specification: dict[str, Any]
    legal_notice: str
