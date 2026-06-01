"""서비스용 agent graph 실행 골격입니다.

Master Router가 정한 route만 실행하고,
각 단계는 adapter를 통해 schema 검증 후 shared state에 병합합니다.

─ 전체 흐름 ─
  run_service_pipeline() 호출
    → route에 있는 agent 이름 순서대로 반복
      → adapter.run(state) : 해당 agent 실행 + 결과 검증
      → state[adapter.state_key] = 결과 저장
      → decide_next_agent(state) : 중간 판단 (사용자 입력 필요한지 체크)
    → 최종 판단 결과를 state["master_decision"]에 저장
    → 완성된 state 반환
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from agents.adapters.base import AgentAdapter
from agents.claim.adapter import ClaimAdapter
from agents.composer.adapter import ComposerAdapter
from agents.drawing.adapter import DrawingAdapter
from agents.master.router import SERVICE_PIPELINE, decide_next_agent
from agents.priorart.adapter import PriorArtAdapter
from agents.validation import AgentValidationError
from agents.specification.adapter import SpecificationAdapter
from agents.state import PatentAgentState, create_initial_state
from agents.summary.adapter import SummaryAdapter

# DEFAULT_PIPELINE은 master/router.py의 SERVICE_PIPELINE과 동일합니다.
# graph 외부에서 이 모듈만 import해도 기본 파이프라인 순서를 알 수 있게 re-export합니다.
DEFAULT_PIPELINE = SERVICE_PIPELINE


def build_default_adapters() -> dict[str, AgentAdapter[Any]]:
    """서비스 graph가 기본으로 사용할 adapter 목록을 만듭니다.

    각 agent마다 adapter 객체를 하나 만들어서
    { "agent 이름" : adapter 객체 } 형태의 dict로 반환합니다.

    adapter가 하는 일:
    1. state에서 필요한 입력을 뽑아 agent에 넘김
    2. agent 실행
    3. 결과를 Pydantic schema로 검증
    4. 검증 통과한 dict를 반환 → state에 저장
    """
    adapters: list[AgentAdapter[Any]] = [
        SummaryAdapter(),       # 요약본 작성 agent
        PriorArtAdapter(),      # 선행기술 검색 agent
        ClaimAdapter(),         # 청구항 작성 agent
        DrawingAdapter(),       # 도면 생성 agent
        SpecificationAdapter(), # 명세서 작성 agent
        ComposerAdapter(),      # 최종 문서 패키징 agent
    ]
    # adapter.agent_name을 key로 사용해서 이름으로 바로 찾을 수 있게 합니다.
    return {adapter.agent_name: adapter for adapter in adapters}


def build_agent_state_key_map(adapters: dict[str, AgentAdapter[Any]]) -> dict[str, str]:
    """adapter.state_key에서 agent 결과 저장 위치 맵을 만듭니다.

    state key의 단일 기준은 각 adapter의 state_key입니다.
    Master Router가 별도 dict를 들고 있으면 claim→claims 같은 매핑이 중복되므로,
    graph/pipeline은 이 helper로 만든 값을 decide_next_agent()에 전달합니다.
    """
    return {agent_name: adapter.state_key for agent_name, adapter in adapters.items()}


def run_service_pipeline(
    user_input: str,
    adapters: dict[str, AgentAdapter[Any]] | None = None,
    *,
    initial_state: PatentAgentState | None = None,
    route: Sequence[str] | None = None,
    enable_llm_repair: bool | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> PatentAgentState:
    """주어진 route만 실행하고 결과를 state에 병합합니다.

    Args:
        user_input: 사용자가 입력한 발명 설명 문자열
        adapters: { agent이름: adapter } dict. None이면 build_default_adapters() 사용.
        initial_state: 이어서 실행할 때 넘기는 기존 state. None이면 새 state 생성.
        route: 실행할 agent 이름 순서. None이면 DEFAULT_PIPELINE 전체 실행.
        enable_llm_repair: LLM repair 기능 켜기/끄기. None이면 환경변수 ENABLE_LLM_REPAIR 참고.
        progress_callback: agent 하나 시작될 때마다 호출되는 콜백. callback(agent_name) 형태.
            pipeline.py에서 Redis 진행 상황 업데이트에 씁니다.

    Returns:
        모든 agent 결과가 담긴 PatentAgentState.
        state["master_decision"]에 최종 라우팅 판단이 저장됩니다.

    Note:
        이 함수는 동기(sync) 함수입니다.
        FastAPI endpoint에서 호출할 때는 asyncio.to_thread()로 감싸야 합니다.
        그렇지 않으면 LLM 호출 동안 서버의 이벤트 루프가 멈춥니다.
    """
    # ── state 준비 ──────────────────────────────────
    # initial_state가 있으면 이어서 실행, 없으면 새로 시작
    state = initial_state or create_initial_state(user_input)
    state["user_input"] = user_input or state.get("user_input", "")

    # workflow 필드가 없을 수도 있으니 안전하게 초기화
    state.setdefault("workflow", {})
    state["workflow"]["status"] = "running"
    state["workflow"].setdefault("errors", [])
    state["workflow"].setdefault("trace", [])

    adapter_map = adapters or build_default_adapters()
    agent_state_keys = build_agent_state_key_map(adapter_map)
    selected_route = tuple(route or DEFAULT_PIPELINE)  # 실행할 agent 이름 순서

    # ── agent 순서대로 실행 ──────────────────────────
    for agent_name in selected_route:
        adapter = adapter_map.get(agent_name)
        state["workflow"]["current_agent"] = agent_name  # type: ignore[typeddict-item]

        if adapter is None:
            # 해당 agent의 adapter가 등록되지 않은 경우 에러를 기록하고 건너뜁니다.
            state["workflow"]["errors"].append(f"adapter not registered: {agent_name}")
            continue

        try:
            # agent 시작 시 콜백 호출 (Redis 진행 상황 업데이트 등)
            if progress_callback is not None:
                try:
                    progress_callback(agent_name)
                except Exception:
                    pass  # 콜백 실패가 파이프라인을 중단시키지 않습니다.

            # adapter.run()이 핵심입니다:
            # 1) state에서 입력 추출  2) agent 실행  3) Pydantic 검증  4) dict 반환
            state[adapter.state_key] = adapter.run(state, enable_llm_repair=enable_llm_repair)  # type: ignore[literal-required]
            state["workflow"]["trace"].append({
                "agent": agent_name,
                "action": "run",
                "summary": "adapter executed",
            })
        except AgentValidationError as exc:
            # schema 검증 실패: 어떤 필드가 왜 틀렸는지 기록하고 파이프라인 중단
            # 해당 agent만 /api/agents/{agent_name}/run 으로 개별 재실행 가능
            state["workflow"]["status"] = "failed"
            state["workflow"]["errors"].append(
                f"{agent_name}: 검증 실패 — {exc.schema_name} / "
                f"재실행: POST /api/agents/{agent_name}/run / "
                f"errors: {exc.validation_errors}"
            )
            return state
        except Exception as exc:
            # 그 외 예외: agent 실행 중 발생한 일반 오류
            state["workflow"]["status"] = "failed"
            state["workflow"]["errors"].append(f"{agent_name}: {type(exc).__name__}: {exc}")
            return state

        # ── 중간 판단: 사용자 입력이 더 필요한가? ──────
        # 예: Summary agent가 "발명 설명이 너무 짧다"고 판단하면 여기서 멈춥니다.
        decision = decide_next_agent(state, agent_state_keys=agent_state_keys)
        if decision.requires_user_input:
            state["workflow"]["status"] = "wait_user"
            state["workflow"]["next_agent"] = "master"
            # master_decision에 "어떤 추가 질문이 필요한지" 저장해서 API 응답에 포함
            state["master_decision"] = decision.model_dump(mode="json")
            return state  # 사용자 응답을 기다리기 위해 여기서 반환

    # ── 파이프라인 완료 처리 ──────────────────────────
    final_decision = decide_next_agent(state, agent_state_keys=agent_state_keys)
    state["workflow"]["status"] = "completed" if final_decision.status == "completed" else "running"
    state["workflow"]["current_agent"] = "master"
    # 다음 agent가 "end"면 review로 (review 구현 후 파이프라인의 마지막 단계)
    state["workflow"]["next_agent"] = final_decision.next_agent if final_decision.next_agent != "end" else "review"
    state["master_decision"] = final_decision.model_dump(mode="json")
    return state
