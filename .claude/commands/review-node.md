# 노드 코드 리뷰

$ARGUMENTS 형식: `노드이름` (예: `/review-node claims`)

`agents/nodes/$ARGUMENTS.py`를 리뷰하고 구체적인 피드백을 제공합니다.

## 리뷰 체크리스트

### 코드 품질
- [ ] `def run(state: PatentAgentState) -> dict` 시그니처 준수
- [ ] 반환 dict의 키가 모두 `agents/state.py` 필드와 일치
- [ ] 타입 힌트 누락 없음
- [ ] 라인 길이 100자 초과 없음 (`uv run ruff check agents/nodes/$ARGUMENTS.py`)
- [ ] 함수/클래스에 역할·입력·출력 docstring 있음

### 에러 처리
- [ ] 외부 API 호출(LLM, KIPRIS)에 `try/except` 처리
- [ ] 예외 발생 시 state 필드에 빈값 또는 기본값 반환 처리

### LLM 프롬프트 (해당하는 경우)
- [ ] 시스템 프롬프트와 사용자 프롬프트가 분리되어 있음
- [ ] 특허법 요건(신규성·진보성·기재불비 방지) 관련 지시가 포함되어 있음
- [ ] 출력 포맷이 명확하게 지정되어 있음

### mock 상태 확인
- [ ] mock 코드는 `# ── mock ──` 주석 블록 안에 있음
- [ ] mock 반환값이 실제 구현과 같은 키를 반환함
- [ ] `# ── 실제 구현 위치 ──` 주석 블록이 있음

### 테스트 확인
- [ ] `tests/agents/test_$ARGUMENTS.py` 존재
- [ ] 테스트가 통과하는지 확인: `uv run pytest tests/agents/test_$ARGUMENTS.py -v`

## 리뷰 결과 형식
```
## $ARGUMENTS 노드 리뷰 결과

### ✅ 잘 된 점
...

### ⚠️ 개선 필요
...

### 🔴 필수 수정
...
```
