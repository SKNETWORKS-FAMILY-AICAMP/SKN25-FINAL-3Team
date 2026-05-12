# Examiner Agent 인터페이스

> `agents/nodes/examiner.py` · `run(state)` 함수

---

## 역할

작성된 청구항을 특허법적 관점에서 심사합니다.
신규성·진보성·기재불비 등의 요건을 검토하고 등록 가능 여부를 판정합니다.

---

## 입력 (State 필드)

| 필드 | 타입 | 설명 |
|---|---|---|
| `claims` | `list[dict]` | 심사할 청구항 목록 (claims 출력) |
| `similar_patents` | `list` | 선행기술 목록 (patent_search 출력, 신규성 판단용) |

---

## 출력 (반환 dict 키)

| 필드 | 타입 | 설명 |
|---|---|---|
| `is_registerable` | `bool` | 등록 가능 여부 |
| `examiner_opinion` | `str` | 심사 의견 전문 |
| `examiner_issues` | `list[dict]` | 문제 있는 청구항 목록 |

### examiner_issues 항목 구조

```python
{
    "claim_number": int,  # 문제 청구항 번호
    "reason": str,        # 거절 사유 (신규성 결여, 진보성 결여, 기재불비 등)
}
```

---

## 재시도 조건

`is_registerable = False`이면 graph.py의 `route_after_examiner()`에 의해 claims로 루프백.
`revision_count >= MAX_REVISION(2)`이면 루프 종료 후 drawing으로 강제 진행.

---

## 구현 시 주의사항

- 심사 기준: 신규성(특허법 제29조 1항), 진보성(제29조 2항), 기재불비(제42조 4항)
- `similar_patents`가 비어있으면 신규성 판단은 생략하고 기재불비만 검토
- `is_registerable = True`이더라도 minor 이슈가 있으면 `examiner_opinion`에 기록
