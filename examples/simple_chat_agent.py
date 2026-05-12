"""
LangGraph 입문 샘플 — 단순 대화 채팅 에이전트
================================================

이 파일은 LangGraph 의 핵심 개념을 최소한의 코드로 보여줍니다.
patent_graph(agents/graph.py)를 이해하기 전에 이 파일을 먼저 읽어보세요.

핵심 개념
---------
1. State      : 에이전트가 공유하는 상태 (딕셔너리)
2. Node       : 상태를 받아 상태를 반환하는 함수
3. Edge       : 노드 간 연결 (일반 / 조건부)
4. Graph      : 노드 + 엣지의 집합
5. Compile    : 그래프를 실행 가능한 Runnable 로 변환

실행 방법
---------
    uv run python examples/simple_chat_agent.py
    # 또는
    python examples/simple_chat_agent.py
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


# ── 1. State 정의 ────────────────────────────────────────────────────────────
# TypedDict 로 에이전트 상태를 정의합니다.
# Annotated[list, add_messages] 는 messages 를 덮어쓰지 않고 누적시킵니다.

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    turn_count: int   # 대화 횟수 추적 (조건부 엣지에서 사용)


# ── 2. Node 정의 ─────────────────────────────────────────────────────────────
# 노드는 State 를 받아 State 의 일부를 반환하는 함수입니다.
# 반환한 키만 업데이트되고, 나머지는 그대로 유지됩니다.

def chat_node(state: ChatState) -> dict:
    """LLM 에 현재 대화 내역을 전달하고 응답을 받습니다."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    system = SystemMessage(content="당신은 특허 명세서 작성을 돕는 친절한 AI 어시스턴트입니다.")
    response = llm.invoke([system] + state["messages"])

    return {
        "messages": [response],           # add_messages 로 누적됨
        "turn_count": state["turn_count"] + 1,
    }


def summarize_node(state: ChatState) -> dict:
    """대화가 길어지면 이전 내용을 요약해 토큰을 절약합니다."""
    llm = ChatOpenAI(model="gpt-4o-mini")

    summary_prompt = HumanMessage(content=(
        "지금까지의 대화를 3문장으로 요약해줘. "
        "중요한 발명 정보가 빠지지 않게 해줘."
    ))
    summary = llm.invoke(state["messages"] + [summary_prompt])

    # 대화 내역을 요약본 하나로 교체
    return {
        "messages": [summary],
        "turn_count": 0,
    }


# ── 3. 조건부 엣지 함수 ───────────────────────────────────────────────────────
# 반환값(문자열)이 path_map 의 키와 매핑됩니다.

def should_continue(state: ChatState) -> str:
    """
    대화를 계속할지, 요약할지, 종료할지 결정합니다.

    반환값 → 다음 노드
    ─────────────────────
    "end"       → END (그래프 종료)
    "summarize" → summarize_node
    "continue"  → chat_node (루프백)
    """
    last_message = state["messages"][-1]
    content = getattr(last_message, "content", "")

    if "종료" in content or "bye" in content.lower():
        return "end"

    if state["turn_count"] >= 5:   # 5턴마다 요약
        return "summarize"

    return "continue"


# ── 4. 그래프 조립 ────────────────────────────────────────────────────────────

def build_chat_graph():
    graph = StateGraph(ChatState)

    # 노드 등록
    graph.add_node("chat",      chat_node)
    graph.add_node("summarize", summarize_node)

    # 진입점
    graph.set_entry_point("chat")

    # 조건부 엣지: chat 이후 분기
    graph.add_conditional_edges(
        "chat",
        should_continue,
        {
            "continue":  "chat",       # 루프백
            "summarize": "summarize",  # 요약 노드로
            "end":       END,          # 종료
        },
    )

    # 요약 후 다시 대화 재개
    graph.add_edge("summarize", "chat")

    return graph.compile()


chat_agent = build_chat_graph()


# ── 5. 실행 예시 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("특허 상담 채팅 에이전트 (종료하려면 '종료' 입력)\n")

    state: ChatState = {"messages": [], "turn_count": 0}

    while True:
        user_input = input("나: ").strip()
        if not user_input:
            continue

        state["messages"].append(HumanMessage(content=user_input))

        result = chat_agent.invoke(state)
        state = result   # 상태 업데이트

        last_ai_message = result["messages"][-1]
        print(f"AI: {last_ai_message.content}\n")

        if "종료" in user_input or "bye" in user_input.lower():
            print("대화를 종료합니다.")
            break
