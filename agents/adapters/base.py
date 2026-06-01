"""서비스 graph와 실제 agent 구현 사이의 공통 adapter 계약을 정의합니다.

각 adapter는 shared state에서 필요한 입력만 뽑아 `state_input`을 만들고,
실제 agent 호출 결과를 Pydantic schema로 검증한 뒤 다시 state에 넣을 dict로 변환합니다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from agents.state import PatentAgentState
from agents.validation import safe_validate_output

OutputModelT = TypeVar("OutputModelT", bound=BaseModel)


class AgentAdapter(ABC, Generic[OutputModelT]):
    """서비스 graph가 호출하는 agent adapter 기본형입니다."""

    agent_name: str
    state_key: str
    schema: type[OutputModelT]
    fallback: OutputModelT

    def build_input(self, state: PatentAgentState) -> Any:
        """agent에 넘길 입력을 만듭니다."""
        return state

    @abstractmethod
    def call_agent(self, state_input: Any) -> Any:
        """실제 agent 구현 또는 임시 skeleton runner를 호출합니다."""

    def normalize_for_state(self, output: OutputModelT) -> dict[str, Any]:
        """검증된 output을 shared state에 저장 가능한 JSON dict로 변환합니다."""
        return output.model_dump(mode="json")

    def run(self, state: PatentAgentState, *, enable_llm_repair: bool | None = None) -> dict[str, Any]:
        """입력 구성, agent 호출, schema 검증, state 저장용 변환을 한 번에 수행합니다."""
        raw_output = self.call_agent(self.build_input(state))
        validated = safe_validate_output(
            agent_name=self.agent_name,
            schema=self.schema,
            raw_output=raw_output,
            fallback=self.fallback,
            enable_llm_repair=enable_llm_repair,
        )
        return self.normalize_for_state(validated)
