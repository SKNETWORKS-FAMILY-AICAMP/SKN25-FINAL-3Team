# 테스트 실행 및 보고

$ARGUMENTS 형식: `노드이름` 또는 비워두면 전체 테스트

## 전체 테스트 실행

```bash
uv run pytest -v --tb=short
```

## 노드별 테스트 실행

```bash
uv run pytest tests/agents/test_$ARGUMENTS.py -v --tb=short
```

## API 통합 테스트

```bash
uv run pytest tests/api/ -v --tb=short
```

## 테스트 후 반드시 확인

1. **PASSED 수 / FAILED 수 / ERROR 수** 를 보고합니다.
2. FAILED 또는 ERROR가 있으면 트레이스백을 읽고 원인을 분석합니다.
3. mock 노드 테스트가 실패하면 — State 필드명이 맞는지 `agents/state.py` 확인.
4. import 오류가 나면 — `agents/nodes/__init__.py` 확인.
5. 모든 테스트 통과 후 결과를 요약 보고합니다.

## 린트 검사도 함께 실행

```bash
uv run ruff check .
```
