# Patent Search Agent 인터페이스

> `agents/nodes/patent_search.py` · `run(state)` 함수

---

## 역할

발명 내용을 바탕으로 KIPRIS 특허 DB에서 선행기술을 검색합니다.
consulting 노드와 병렬로 실행되며 IPC 코드를 자동 분류합니다.

---

## 입력 (State 필드)

| 필드 | 타입 | 설명 |
|---|---|---|
| `invention_flow` | `str` | 발명의 전체 흐름 |
| `problem` | `str` | 기존 발명의 문제점 |

---

## 출력 (반환 dict 키)

| 필드 | 타입 | 설명 |
|---|---|---|
| `similar_patents` | `list[dict]` | 유사 특허 목록 |
| `ipc_codes` | `list[str]` | 검색에 사용된 IPC 코드 목록 |

### similar_patents 항목 구조

```python
{
    "id": str,                  # 특허 등록/공개 번호
    "title": str,               # 발명 명칭
    "similarity": float,        # 유사도 0.0 ~ 1.0
    "summary_problem": str,     # 선행특허의 문제점
    "summary_solution": str,    # 선행특허의 해결수단
}
```

---

## 구현 시 주의사항

- KIPRIS API는 `agents/tools/kipris_api.py`를 통해서만 호출 (직접 호출 금지)
- IPC 코드는 LLM으로 발명 내용을 분석해 자동 분류
- 최대 10개 선행특허 반환 권장
- API 오류 시 `similar_patents = []`, `ipc_codes = []` 반환 (파이프라인 계속 진행)
