# State 동기화 검사

`agents/state.py`의 `PatentAgentState`와 `agents/graph.py`의 실제 사용이 일치하는지 전수 검사합니다.

## 검사 절차

### 1. State 전체 필드 목록 추출
```bash
cat agents/state.py
```
`PatentAgentState`의 모든 필드와 타입을 목록화합니다.

### 2. 각 노드의 반환 필드 추출
```bash
grep -A 20 "def run" agents/nodes/*.py | grep -v "mock" | grep '^\s*"'
```
각 노드가 실제로 반환하는 dict 키를 수집합니다.

### 3. 불일치 항목 식별
- **State에 있지만 어떤 노드도 채우지 않는 필드** → 불필요한 필드이거나 구현 누락
- **노드가 반환하지만 State에 없는 키** → State 미등록 (LangGraph가 무시하거나 오류)
- **타입이 맞지 않는 경우** → 런타임 오류 가능성

### 4. graph.py 엣지 검사
```bash
cat agents/graph.py
```
- 모든 노드가 `add_node()`로 등록되어 있는지
- 고립된 노드(엣지가 없는 노드)가 있는지
- `revision_count` 필드가 `route_after_examiner`에서 올바르게 읽히는지

### 5. 결과 보고
```
## State 동기화 검사 결과

### 필드 현황
| 필드명 | State 존재 | 채우는 노드 | 상태 |
|---|---|---|---|
...

### 발견된 문제
...

### 권장 수정사항
...
```
