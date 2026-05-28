"""이 파일은 graph/state와 실제 agent.py 사이의 adapter 기본 계약을 정의하는 파일이다.

adapter는 state에서 입력을 추출하고, agent 실행 결과를 schema 검증 후
다시 state에 저장 가능한 형태로 변환한다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from agents.state import PatentAgentState
from agents.validation import safe_validate_output

OutputModelT = TypeVar("OutputModelT", bound=BaseModel)


class AgentAdapter(ABC, Generic[OutputModelT]):
    """서비스형 graph가 호출하는 agent adapter 기본형."""

    agent_name: str
    state_key: str
    schema: type[OutputModelT]
    fallback: OutputModelT

    def build_input(self, state: PatentAgentState) -> Any:
        """agent.py에 넘길 입력 payload를 만든다."""

        return state

    @abstractmethod
    def call_agent(self, payload: Any) -> Any:
        """실제 agent.py runner/API 호출."""

    def normalize_for_state(self, output: OutputModelT) -> dict[str, Any]:
        """검증된 Pydantic output을 state에 저장할 JSON dict로 변환."""

        return output.model_dump(mode="json")

    def run(self, state: PatentAgentState, *, enable_llm_repair: bool | None = None) -> dict[str, Any]:
        payload = self.build_input(state)
        raw_output = self.call_agent(payload)
        validated = safe_validate_output(
            agent_name=self.agent_name,
            schema=self.schema,
            raw_output=raw_output,
            fallback=self.fallback,
            enable_llm_repair=enable_llm_repair,
        )
        return self.normalize_for_state(validated)
