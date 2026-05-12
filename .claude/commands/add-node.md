# 새 에이전트 노드 추가

$ARGUMENTS 형식: `노드이름` (예: `/add-node summarizer`)

새 LangGraph 노드를 파이프라인에 추가합니다. 아래 순서대로 진행합니다.

## 작업 순서

### 1. 노드 파일 생성
`agents/nodes/$ARGUMENTS.py` 를 생성합니다.

```python
"""
$ARGUMENTS 노드

역할: (한 문장으로 역할 작성)
입력: PatentAgentState의 어떤 필드를 사용하는지
출력: 어떤 필드를 반환하는지
"""
from agents.state import PatentAgentState


def run(state: PatentAgentState) -> dict:
    # ── mock ─────────────────────────────────────────────────────────────
    return {
        # 출력 필드 작성
    }
    # ── 실제 구현 위치 ──────────────────────────────────────────────────
    # 실제 구현 코드
```

### 2. State 필드 추가
`agents/state.py`의 `PatentAgentState`에 이 노드의 출력 필드를 추가합니다.
- **주의**: State 변경은 팀 합의 사항입니다. 필드 추가 전 CLAUDE.md 섹션 6 확인.

### 3. graph.py 등록
`agents/graph.py`의 `build_graph()` 함수에 노드와 엣지를 추가합니다.

```python
graph.add_node("$ARGUMENTS", $ARGUMENTS.run)
graph.add_edge("이전노드", "$ARGUMENTS")
graph.add_edge("$ARGUMENTS", "다음노드")
```

`agents/nodes/__init__.py`에 import도 추가합니다.

### 4. API 라우터 추가
`api/routers/$ARGUMENTS.py`를 생성하고 `api/main.py`에 등록합니다.

### 5. 테스트 작성
`tests/agents/test_$ARGUMENTS.py`를 생성합니다.
- `tests/fixtures/` 의 샘플 state를 활용해 기본 단위 테스트 작성
- mock 상태에서도 반환 필드가 올바른지 검증

### 6. 인터페이스 문서 작성
`docs/interfaces/$ARGUMENTS.md`를 생성합니다.

### 7. CLAUDE.md 모듈 맵 업데이트
CLAUDE.md 섹션 3의 모듈 맵 테이블에 신규 노드를 추가합니다.

### 8. 검증
```bash
uv run pytest tests/agents/test_$ARGUMENTS.py -v
uv run ruff check agents/nodes/$ARGUMENTS.py
```
