# ADR 003 — 멀티턴 챗봇 상담 설계

날짜: 2026-05
상태: 결정됨

---

## 맥락

최종 서비스는 단순 API 호출이 아닌, 사용자가 챗봇 UI를 통해 AI와 여러 번 대화하며 발명 내용을 구체화하는 **대화형 서비스**입니다. 이 요건이 아키텍처 전반에 영향을 줍니다.

## 핵심 결정 사항

### 1. 파이프라인을 Phase 1 / Phase 2로 분리

- **Phase 1 (상담)**: consulting 노드를 여러 번 호출하는 대화 루프. UI와 실시간 상호작용.
- **Phase 2 (생성)**: `is_consultation_done=True` 신호를 받아 자동 실행되는 명세서 생성 파이프라인.

두 페이즈는 같은 `PatentAgentState`를 공유하지만 실행 트리거가 다릅니다.

### 2. 상담 완료 신호: `is_consultation_done` 필드

consulting 노드가 발명 정보가 충분하다고 판단하면 `is_consultation_done=True`를 반환합니다.
`route_after_consulting()` 라우터가 이 필드를 보고 Phase 2로 전환합니다.

```python
# agents/state.py에 추가 필요 (팀 합의 후)
is_consultation_done: bool
next_question: str   # UI에 표시할 AI 응답 메시지
```

### 3. 세션 영속성: LangGraph Checkpointer

멀티턴 대화는 HTTP 요청 사이에 state를 유지해야 합니다.

**채택: LangGraph MemorySaver (개발/프로토타입) → SQLite/PostgreSQL Checkpointer (프로덕션)**

```python
# api/main.py
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
patent_graph = build_graph().compile(checkpointer=checkpointer)

# 각 API 호출 시 같은 thread_id(= session_id)로 invoke
result = patent_graph.invoke(
    {"user_input": message},
    config={"configurable": {"thread_id": session_id}},
)
```

이렇게 하면 같은 `session_id`로 호출할 때마다 이전 state가 자동으로 복원됩니다.

### 4. API 설계: 메시지 단위 POST

챗봇 UI는 사용자 메시지마다 `POST /consult`를 호출합니다. 세션 관리는 서버가 담당합니다.

```
POST /consult
{ "session_id": "uuid", "user_id": "...", "message": "..." }

→ { "reply": "AI 응답", "is_done": false }
→ { "reply": "명세서 작성 시작", "is_done": true }  ← Phase 2 트리거
```

`is_done=true` 응답을 받은 UI는 로딩 상태를 보여주고, 완성된 명세서를 별도 폴링/웹소켓으로 수신합니다.

### 5. UI 스트리밍 (LangChain astream_events 활용)

LLM 응답을 토큰 단위로 스트리밍하면 UX가 크게 향상됩니다.

```python
# FastAPI + SSE (Server-Sent Events) 또는 WebSocket
async for event in patent_graph.astream_events(input, config=...):
    if event["event"] == "on_chat_model_stream":
        yield event["data"]["chunk"].content
```

## 영향 받는 파일

| 파일 | 변경 내용 |
|---|---|
| `agents/state.py` | `is_consultation_done: bool`, `next_question: str` 필드 추가 |
| `agents/graph.py` | `route_after_consulting()` 로직 업데이트, `await_user` 경로 추가 |
| `agents/nodes/consulting.py` | 멀티턴 로직 구현, 상담 완료 판단 LLM 호출 |
| `api/main.py` | LangGraph Checkpointer 연동 |
| `api/routers/consulting.py` | `POST /consult` 엔드포인트 — 메시지 수신, state invoke, 응답 반환 |

## 대안 (채택하지 않은 이유)

- **프론트엔드에서 대화 이력 관리**: 클라이언트가 매 요청마다 전체 이력을 전송해야 해 payload가 커지고, 서버에서 이력 저장이 어려움.
- **WebSocket 전용**: 구현 복잡도 증가. SSE + REST 조합으로 충분한 UX 확보 가능.
