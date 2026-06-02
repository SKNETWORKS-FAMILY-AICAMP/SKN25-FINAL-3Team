"""서비스 graph와 실제 agent 구현 사이의 공통 adapter 계약을 정의합니다.

─ Adapter 패턴이란? ─
  graph.py는 각 agent가 어떻게 구현됐는지 몰라도 됩니다.
  "adapter.run(state)를 호출하면 결과가 나온다"는 것만 알면 됩니다.
  실제 agent 구현(LLM 호출, DB 검색 등)은 각 adapter의 call_agent()가 담당합니다.

  비유: 콘센트(adapter)와 플러그(agent)의 관계.
  콘센트 모양(인터페이스)만 맞으면 어떤 전기기기(agent)든 꽂을 수 있습니다.

─ 제네릭(Generic)이란? ─
  AgentAdapter[OutputModelT]에서 OutputModelT는 "이 adapter가 반환하는 Pydantic 모델 타입"입니다.
  예: SummaryAdapter는 AgentAdapter[SummaryAgentOutput]을 상속합니다.
  이렇게 하면 IDE가 "이 adapter의 결과는 SummaryAgentOutput이다"를 알 수 있습니다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from agents.state import PatentAgentState
from agents.validation import safe_validate_output

OutputModelT = TypeVar("OutputModelT", bound=BaseModel)


class AgentAdapter(ABC, Generic[OutputModelT]):
    """서비스 graph가 호출하는 agent adapter 기본형입니다.

    ABC(Abstract Base Class): 이 클래스는 직접 쓰는 게 아니라 상속해서 씁니다.
    @abstractmethod가 붙은 메서드는 반드시 하위 클래스에서 구현해야 합니다.

    각 agent(summary, claim 등)는 이 클래스를 상속하는 자신만의 adapter를 만듭니다.
    하위 클래스에서 반드시 정의해야 하는 클래스 변수:
      - agent_name : agent 식별 이름 (예: "summary")
      - state_key  : state에서 결과를 저장할 key (예: "summary", "claims")
      - schema     : 결과 검증에 쓸 Pydantic 모델 클래스
    """

    agent_name: str              # agent 식별 이름. build_default_adapters()의 key로 사용됩니다.
    state_key: str               # state에서 결과를 저장할 key. Master Router 판단의 단일 기준입니다.
    schema: type[OutputModelT]   # 결과를 검증할 Pydantic 모델 클래스 (예: SummaryAgentOutput)

    def build_input(self, state: PatentAgentState) -> Any:
        """agent에 넘길 입력을 state에서 뽑아 만듭니다.

        기본 구현은 state 전체를 그대로 넘깁니다.
        필요한 경우 하위 클래스에서 오버라이드해서 필요한 필드만 뽑아 줍니다.
        """
        return state

    @abstractmethod
    def call_agent(self, state_input: Any) -> Any:
        """실제 agent 구현 또는 임시 skeleton runner를 호출합니다.

        @abstractmethod: 하위 클래스에서 반드시 구현해야 합니다.
        이 메서드 안에서 LLM API 호출, DB 검색 등 실제 agent 로직이 들어갑니다.
        """

    def normalize_for_state(self, output: OutputModelT) -> dict[str, Any]:
        """검증된 output을 shared state에 저장 가능한 JSON dict로 변환합니다."""
        return output.model_dump(mode="json")

    def run(self, state: PatentAgentState, *, enable_llm_repair: bool | None = None) -> dict[str, Any]:
        """입력 구성 → agent 호출 → schema 검증 → state 저장용 변환을 한 번에 수행합니다.

        graph.py에서 호출하는 메인 메서드입니다. 전체 흐름:
        1. build_input(state)    : state에서 필요한 입력 추출
        2. call_agent(input)     : 실제 agent 실행 (LLM 호출 등)
        3. safe_validate_output(): Pydantic 검증 → 실패 시 AgentValidationError 발생
        4. normalize_for_state() : 검증된 모델을 dict로 변환
        5. dict 반환 → graph.py가 state[state_key]에 저장

        검증 실패 시 AgentValidationError가 발생하고,
        graph.py의 except 블록이 이를 잡아 파이프라인을 중단합니다.
        """
        raw_output = self.call_agent(self.build_input(state))
        validated = safe_validate_output(
            agent_name=self.agent_name,
            schema=self.schema,
            raw_output=raw_output,
            enable_llm_repair=enable_llm_repair,
        )
        return self.normalize_for_state(validated)
