"""Master Agent output schema.

현재 서비스 라우팅은 MasterDecision (agents/master/router.py)이 담당합니다.
이 스키마는 Master Agent가 자체 LLM 판단 결과를 반환할 때 사용하는 계약입니다.
"""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from agents.schemas.common import AgentOutputBase


MasterStage = Literal[
    "input_collection",
    "summary_generation",
    "summary_feedback",
    "default_pipeline",
    "completed",
    "failed",
]

MasterAction = Literal[
    "collect_input",
    "run_summary",
    "wait_feedback",
    "revise_summary",
    "run_next_agent",
    "complete",
    "fail",
]


class MasterAgentOutput(AgentOutputBase):
    """Master Agent의 LLM 판단 결과 schema입니다."""

    stage: MasterStage = Field(..., description="현재 진행 단계")
    action: MasterAction = Field(..., description="다음 수행 동작")

    current_agent: str = Field("", description="현재 실행 중인 agent")
    next_agent: str = Field("", description="다음 실행할 agent")
    pipeline_index: int = Field(0, description="SERVICE_PIPELINE에서 현재 위치")

    summary_accepted: bool = Field(False, description="사용자가 요약본을 승인했는지 여부")
    feedback_required: bool = Field(False, description="요약본 수정 피드백이 필요한지 여부")
    route_reason: str = Field("", description="현재 action을 선택한 간단한 이유")
