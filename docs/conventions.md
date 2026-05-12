# 코딩 컨벤션

> 코딩 에이전트와 팀원 모두가 따르는 규칙입니다.
> 이 파일에 없는 내용은 PEP 8 + ruff 기본 설정을 따릅니다.

---

## 1. 노드 함수 구조

모든 LangGraph 노드 파일은 아래 구조를 따릅니다.

```python
"""
노드 이름 (예: Claims Agent 노드)

역할: 한 문장으로 이 노드가 하는 일
입력: state에서 읽는 필드 목록
출력: state에 쓰는 필드 목록
Side effects: DB 저장, 외부 API 호출 등 (없으면 None)
"""
from agents.state import PatentAgentState


def run(state: PatentAgentState) -> dict:
    """
    Args:
        state: 파이프라인 공유 상태

    Returns:
        변경된 State 필드만 담은 dict
        (전체 state를 반환하지 않습니다)
    """
    # ── mock ─────────────────────────────────────────────────────────────────
    return {
        "출력필드": "mock 값",
    }
    # ── 실제 구현 위치 ────────────────────────────────────────────────────────
    # 실제 구현 코드
```

### 규칙
- 함수명은 반드시 `run` (LangGraph 노드 등록 컨벤션)
- 반환값은 **변경된 필드만** dict로 반환 (전체 state 반환 금지)
- mock 블록은 `# ── mock ──` 주석 구분선으로 감싸기
- 실제 구현 시 mock 블록 제거, `# ── 실제 구현 위치 ──` 블록에 작성

---

## 2. 타입 힌트

모든 함수의 매개변수와 반환값에 타입 힌트를 명시합니다.

```python
# ✅ 올바른 예
def search_by_ipc(ipc_code: str, keyword: str) -> list[dict]:
    ...

def get_patent_detail(patent_id: str) -> dict | None:
    ...

# ❌ 잘못된 예
def search_by_ipc(ipc_code, keyword):
    ...
```

복잡한 반환 타입은 `TypedDict` 또는 `dataclass`로 정의합니다.

```python
from typing import TypedDict

class PatentSummary(TypedDict):
    id: str
    title: str
    similarity: float
    summary_problem: str
    summary_solution: str
```

---

## 3. 에러 처리

외부 API 호출(LLM, KIPRIS, DB)은 반드시 `try/except`로 감쌉니다.

```python
# ✅ 올바른 예
def run(state: PatentAgentState) -> dict:
    try:
        result = llm.invoke(prompt)
        return {"invention_flow": result.content}
    except Exception as e:
        # 에러 시 빈값 반환 → 파이프라인은 계속 진행
        return {
            "invention_flow": "",
            "problem": f"[오류] LLM 호출 실패: {e}",
        }

# ❌ 잘못된 예 — 예외를 그냥 올려보내면 파이프라인 전체 중단
def run(state: PatentAgentState) -> dict:
    result = llm.invoke(prompt)  # 실패 시 그래프 전체 중단됨
    return {"invention_flow": result.content}
```

---

## 4. LLM 프롬프트 작성

### 시스템/사용자 프롬프트 분리

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatOpenAI(model="gpt-4o", temperature=0)

system_prompt = """
당신은 특허 전문 변리사입니다.
[역할과 출력 형식 지시]
"""

user_prompt = f"""
발명 정보:
- 발명 흐름: {state['invention_flow']}
- 문제점: {state['problem']}
"""

response = llm.invoke([
    SystemMessage(content=system_prompt),
    HumanMessage(content=user_prompt),
])
```

### 출력 포맷 명시

LLM이 구조화된 출력을 반환해야 할 때는 JSON 형식을 명시합니다.

```python
system_prompt = """
...
반드시 아래 JSON 형식으로만 응답하세요:
{
  "claim_number": 1,
  "claim_type": "method",
  "content": "청구항 내용"
}
"""
```

---

## 5. 임포트 순서

ruff의 isort 규칙을 따릅니다.

```python
# 1. 표준 라이브러리
import os
from typing import Optional

# 2. 서드파티
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

# 3. 프로젝트 내부
from agents.state import PatentAgentState
from agents.tools.kipris_api import search_by_ipc
```

---

## 6. 네이밍 컨벤션

| 대상 | 규칙 | 예시 |
|---|---|---|
| 함수 | snake_case | `run`, `search_by_ipc` |
| 클래스 | PascalCase | `PatentAgentState`, `KiprisClient` |
| 상수 | UPPER_SNAKE_CASE | `MAX_REVISION = 2` |
| 파일 | snake_case | `patent_search.py` |
| 노드 이름 (graph) | snake_case | `"patent_search"` |

---

## 7. 테스트 작성

### 파일 위치
- 노드 단위 테스트: `tests/agents/test_노드이름.py`
- API 통합 테스트: `tests/api/test_엔드포인트.py`
- 공용 fixture: `tests/conftest.py`
- 샘플 데이터: `tests/fixtures/`

### 테스트 구조

```python
import pytest
from agents.state import PatentAgentState
from agents.nodes import consulting


# 기본 fixture (tests/fixtures/sample_state.py 또는 conftest.py에서 가져옴)
@pytest.fixture
def base_state() -> PatentAgentState:
    return {
        "user_input": "IoT 기반 스마트 주차 시스템",
        "user_id": "test-user",
        "session_id": "test-session",
        # ... 나머지 필드는 빈값
    }


def test_run_returns_required_fields(base_state):
    """run()이 반드시 반환해야 하는 필드를 포함하는지 검증"""
    result = consulting.run(base_state)
    assert "invention_flow" in result
    assert "problem" in result
    assert "differentiation" in result
    assert "effect" in result
    assert "raw_conversation" in result


def test_run_returns_non_empty_strings(base_state):
    """mock 상태에서도 빈 문자열을 반환하지 않는지 검증"""
    result = consulting.run(base_state)
    assert len(result["invention_flow"]) > 0
```

---

## 8. 커밋 메시지

```
feat(노드명): 기능 추가 한 줄 요약
fix(노드명): 버그 수정 한 줄 요약
refactor(노드명): 리팩터링 한 줄 요약
test: 테스트 추가 또는 수정
docs: 문서 업데이트
chore: 설정, 의존성 등 코드 외 변경
```

예시:
```
feat(claims): 독립항 3종 자동 생성 구현
fix(examiner): revision_count 초기화 누락 수정
docs: consulting 노드 인터페이스 문서 추가
```
