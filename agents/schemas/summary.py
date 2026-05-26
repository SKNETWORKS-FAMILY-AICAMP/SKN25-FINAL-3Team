"""요약본작성 Summary Agent output schema.

중간발표 MVP에서는 5개 inventor input을 받아
사람이 확인할 요약본과 후속 agent가 읽을 구조화 발명 정보를 만든다.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from agents.schemas.common import AgentOutputBase


class InventorInput(BaseModel):
    """사용자가 최초 입력하는 5개 필드."""

    project_name: str = Field(..., description="프로젝트명 또는 발명 명칭 후보")
    problem_to_solve: str = Field(..., description="해결하고자 하는 문제 또는 과제")
    prior_art_problem: str = Field(..., description="기존 기술의 문제점")
    core_technology: str = Field(..., description="핵심 기술 구성 또는 해결 수단")
    expected_effect: str = Field(..., description="발명의 효과")


class SummaryComponent(BaseModel):
    """요약 단계에서 식별한 구성요소 후보."""

    name: str = Field(..., description="구성요소 이름")
    role: str = Field("", description="구성요소의 역할")
    effect: str = Field("", description="해당 구성요소가 기여하는 효과")
    related_inputs: list[str] = Field(default_factory=list, description="구성요소가 사용하는 입력 데이터")
    related_outputs: list[str] = Field(default_factory=list, description="구성요소가 만드는 출력/결과")
    evidence: str = Field("", description="5개 입력 중 근거가 된 문장")


class SummaryEffect(BaseModel):
    """명세서 Agent가 활용할 원인-효과 구조."""

    effect: str = Field(..., description="발명의 효과")
    cause: str = Field("", description="그 효과가 발생하는 기술적 원인")
    related_elements: list[str] = Field(default_factory=list, description="효과와 연결되는 구성요소/단계")
    evidence: str = Field("", description="효과/원인을 뒷받침하는 입력 근거")


class TermCandidate(BaseModel):
    """document_links.term_registry로 승격될 수 있는 용어 후보."""

    id: str = Field("", description="C001 같은 내부 후보 ID")
    canonical_name: str = Field(..., description="표준 용어 후보")
    aliases: list[str] = Field(default_factory=list, description="동일 대상을 가리키는 별칭 후보")
    source: str = Field("", description="용어 후보가 나온 입력/필드")


class SummaryProcessStep(BaseModel):
    """요약 단계에서 식별한 처리 단계 후보."""

    order: int = Field(..., description="처리 순서")
    name: str = Field(..., description="단계 이름")
    description: str = Field("", description="단계 설명")
    input_data: list[str] = Field(default_factory=list)
    output_data: list[str] = Field(default_factory=list)


class StructuredInvention(BaseModel):
    """후속 claim/drawing/prior_art/specification agent가 공통으로 읽는 발명 구조."""

    title: str = Field("", description="발명 명칭 후보")
    technical_field_natural: str = Field("", description="IPC 코드가 아닌 자연어 기술분야 문장")
    background: list[str] = Field(default_factory=list, description="사용 맥락/배경기술 후보")
    use_cases: list[str] = Field(default_factory=list, description="발명이 적용될 수 있는 사용 사례")

    problem: str = Field("", description="발명이 해결하려는 문제")
    prior_art_problem: str = Field("", description="기존 기술의 문제점")
    solution: str = Field("", description="핵심 해결 수단")

    components: list[SummaryComponent] = Field(default_factory=list)
    process_steps: list[SummaryProcessStep] = Field(default_factory=list)

    input_data: list[str] = Field(default_factory=list)
    output_result: list[str] = Field(default_factory=list)

    technical_features: list[str] = Field(default_factory=list)
    differentiators: list[str] = Field(default_factory=list)
    expected_effects: list[str] = Field(default_factory=list, description="호환용 단순 효과 목록")
    effects: list[SummaryEffect] = Field(default_factory=list, description="원인-효과-관련요소 구조화 효과")

    missing_slots: list[str] = Field(default_factory=list, description="입력만으로 부족한 정보 항목")
    clarification_questions: list[str] = Field(default_factory=list, description="사용자에게 물어볼 추가 질문 후보")
    term_registry_seed: list[TermCandidate] = Field(default_factory=list, description="용어 통일을 위한 초기 후보")

    application_domain: str = Field("", description="적용 분야")
    ai_techniques: list[str] = Field(default_factory=list, description="AI/소프트웨어 기술 키워드")


class SummaryAgentOutput(AgentOutputBase):
    """요약본작성 agent의 검증용 output 계약."""

    project_name: str = Field("", description="프로젝트명")
    problem_to_solve: str = Field("", description="해결하고자 하는 문제")
    prior_art_problem: str = Field("", description="기존 기술의 문제점")
    core_technology: str = Field("", description="핵심 기술 구성")
    expected_effect: str = Field("", description="발명의 효과")

    readable_summary: str = Field("", description="사용자가 확인할 수 있는 사람이 읽기 쉬운 발명 요약본")
    structured_invention: StructuredInvention = Field(
        default_factory=StructuredInvention,
        description="후속 agent들이 state에서 읽을 구조화 발명 정보",
    )

    feedback_applied: list[str] = Field(default_factory=list, description="반영된 사용자 피드백")
    warnings: list[str] = Field(default_factory=list, description="입력만으로 확정하기 어려운 부분")
