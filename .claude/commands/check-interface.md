# 노드 인터페이스 계약 검증

$ARGUMENTS 형식: `노드이름` 또는 비워두면 전체 노드 검사

모든 노드가 인터페이스 계약을 올바르게 구현하고 있는지 확인합니다.

## 검사 항목

### 1. 함수 시그니처 확인
각 `agents/nodes/*.py` 파일이 아래 시그니처를 가지는지 확인합니다:
```python
def run(state: PatentAgentState) -> dict:
```

```bash
grep -n "def run" agents/nodes/*.py
```

### 2. State 필드 일관성 확인
노드가 반환하는 dict 키가 `agents/state.py`의 `PatentAgentState` 필드와 일치하는지 확인합니다.

- `agents/state.py`에서 전체 필드 목록을 읽습니다.
- 각 노드의 `return {}` 블록에서 반환 키를 추출합니다.
- State에 없는 키를 반환하는 노드가 있으면 경고합니다.

### 3. graph.py 등록 확인
`agents/nodes/` 에 있는 모든 노드가 `agents/graph.py`의 `build_graph()`에 `add_node()`로 등록되어 있는지 확인합니다.

```bash
grep "add_node" agents/graph.py
ls agents/nodes/*.py
```

### 4. 인터페이스 문서 존재 여부
각 노드에 대응하는 `docs/interfaces/노드이름.md`가 있는지 확인합니다.

```bash
ls docs/interfaces/
ls agents/nodes/
```

### 5. 결과 보고
- ✅ 계약 준수 노드 목록
- ⚠️ 문제 발견된 노드와 구체적인 사유
- 수정이 필요한 경우 수정 방법 제시
