# Consulting Agent 인터페이스

> `agents/nodes/consulting.py` · `run(state)` 함수

---

## 역할

사용자와 **멀티턴 대화**를 통해 발명의 핵심 요소를 추출합니다.

- 발명 내용이 충분히 파악되면 `is_consultation_done = True`를 반환해 명세서 생성 파이프라인으로 전환합니다.
- 정보가 부족하면 `next_question`에 추가 질문을 담아 반환하고, UI는 이를 사용자에게 표시합니다.
- 사용자가 답변을 보내면 다시 이 노드가 호출됩니다. (루프)

### 대화 흐름 예시

```
[사용자] IoT로 주차 시스템을 만들었어요.
[AI]     어떤 센서를 사용하셨나요? 기존 주차 시스템과의 차별점은 무엇인가요?
[사용자] 초음파 센서입니다. 기존과 달리 AI로 빈자리를 예측해요.
[AI]     발명의 주요 효과나 기대 성능이 있으신가요?
[사용자] 주차 탐색 시간을 70% 줄일 수 있어요.
[AI]     감사합니다. 이제 명세서 작성을 시작하겠습니다.  ← is_consultation_done=True
```

---

## 입력 (State 필드)

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `user_input` | `str` | ✅ | 현재 사용자 메시지 |
| `raw_conversation` | `list` | ✅ | 지금까지의 전체 대화 이력 (누적) |
| `user_id` | `str` | ✅ | 사용자 식별자 (DB 저장용) |
| `session_id` | `str` | ✅ | 세션 식별자 (대화 이력 구분) |

---

## 출력 (반환 dict 키)

### 대화 진행 중 (is_consultation_done=False)

| 필드 | 타입 | 설명 |
|---|---|---|
| `raw_conversation` | `list` | 이번 턴의 user·assistant 메시지 추가 |
| `next_question` | `str` | 사용자에게 보여줄 다음 질문 |
| `is_consultation_done` | `bool` | `False` |

### 상담 완료 (is_consultation_done=True)

| 필드 | 타입 | 설명 |
|---|---|---|
| `raw_conversation` | `list` | 최종 대화 이력 |
| `next_question` | `str` | 완료 안내 메시지 (예: "명세서 작성을 시작합니다") |
| `is_consultation_done` | `bool` | `True` → graph.py가 Phase 2로 라우팅 |
| `invention_flow` | `str` | 발명의 전체 흐름 요약 |
| `problem` | `str` | 기존 발명의 문제점 |
| `differentiation` | `str` | 기존 발명과의 차별점 |
| `effect` | `str` | 발명의 효과 |

> `is_consultation_done=True`일 때만 `invention_flow` 등 명세서 생성용 필드를 반환합니다.
> 진행 중에는 이 필드들을 반환하지 않아도 됩니다.

---

## graph.py 라우팅

`route_after_consulting()` 함수가 아래 로직으로 분기합니다:

```python
def route_after_consulting(state: PatentAgentState) -> str:
    if not state.get("is_consultation_done", False):
        return "await_user"   # UI로 next_question 반환, 다음 사용자 입력 대기
    return "proceed"           # patent_search + claims 병렬 실행
```

> ⚠️ `is_consultation_done`과 `next_question` 필드는 현재 `agents/state.py`에 없습니다.
> consulting 노드 구현 시 팀 합의 후 추가하고, `graph.py` 라우터도 함께 수정하세요.

---

## API 엔드포인트 (api/routers/consulting.py)

챗봇 UI는 사용자 메시지마다 아래 API를 호출합니다:

```
POST /consult
Content-Type: application/json

{
  "user_input": "사용자가 입력한 메시지",
  "user_id": "user123",
  "session_id": "uuid"
}
```

**응답 (`api/schemas/patent.py` · `ConsultResponse`):**
```json
{
  "is_consultation_done": false,
  "next_question": "AI의 다음 질문 또는 완료 메시지",
  "invention_flow": null,
  "problem": null,
  "differentiation": null,
  "effect": null
}
```

- `is_consultation_done=false`: `next_question`을 UI에 표시하고 다음 사용자 입력을 기다립니다.
- `is_consultation_done=true`: `invention_flow` 등 명세서 생성용 필드가 채워집니다. UI는 "명세서 생성 중" 로딩 상태로 전환합니다.

---

## 세션 영속성

멀티턴 대화는 서버 재시작에도 이어져야 합니다:

- `session_id`를 키로 DB에 `raw_conversation`을 저장합니다.
- API 서버 재시작 후에도 같은 `session_id`로 대화를 이어갈 수 있어야 합니다.
- LangGraph의 `MemorySaver` 또는 외부 DB checkpointer 사용을 검토하세요.
- 상세 설계: `docs/decisions/003-multiturn-session.md` 참조

---

## 상담 종료 판단 기준 (LLM 프롬프트에 명시)

아래 4가지 정보가 모두 충분히 확보되면 `is_consultation_done=True`를 반환합니다:

1. **발명 흐름** — 발명이 어떻게 동작하는지 전체 흐름이 파악됨
2. **문제점** — 기존 방식의 한계가 구체적으로 설명됨
3. **차별점** — 본 발명만의 특징이 명확함
4. **효과** — 발명으로 인한 구체적인 이점이 제시됨

---

## mock 구현 패턴

```python
def run(state: PatentAgentState) -> dict:
    # ── mock ─────────────────────────────────────────────────────────────────
    conversation = state.get("raw_conversation", [])

    # 3턴(user/assistant 쌍 3회) 이상이면 상담 완료로 처리
    if len(conversation) >= 6:
        return {
            "raw_conversation": [
                {"role": "user", "content": state["user_input"]},
                {"role": "assistant", "content": "상담이 완료되었습니다. 명세서 작성을 시작합니다."},
            ],
            "next_question": "상담이 완료되었습니다. 명세서 작성을 시작합니다.",
            "is_consultation_done": True,
            "invention_flow": f"[MOCK] '{state['user_input']}' 기반 발명 흐름 요약",
            "problem": "[MOCK] 기존 방식의 문제점",
            "differentiation": "[MOCK] 본 발명의 차별점",
            "effect": "[MOCK] 발명의 효과",
        }

    return {
        "raw_conversation": [
            {"role": "user", "content": state["user_input"]},
            {"role": "assistant", "content": "[MOCK] 발명에 대해 더 자세히 설명해 주세요."},
        ],
        "next_question": "[MOCK] 발명에 대해 더 자세히 설명해 주세요.",
        "is_consultation_done": False,
    }
    # ── 실제 구현 위치 ────────────────────────────────────────────────────────
    # LLM으로 대화 이력 분석 → 4가지 정보 충분 여부 판단 → 질문 생성 또는 완료 처리
```
