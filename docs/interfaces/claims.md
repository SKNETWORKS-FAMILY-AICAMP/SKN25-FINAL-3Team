# Claims Agent 인터페이스

> `agents/nodes/claims.py` · `run(state)` 함수

---

## 역할

발명의 핵심 내용을 바탕으로 방법/시스템/기록매체 청구항을 작성합니다.
독립항과 종속항을 포함하며, 권리범위 최대화를 목표로 합니다.

---

## 입력 (State 필드)

| 필드 | 타입 | 설명 |
|---|---|---|
| `invention_flow` | `str` | 발명의 전체 흐름 (consulting 출력) |
| `differentiation` | `str` | 기존 발명과의 차별점 (consulting 출력) |
| `effect` | `str` | 발명의 효과 (consulting 출력) |
| `examiner_issues` | `list` | 심사관 지적 사항 (재작성 시 참조) |
| `revision_count` | `int` | 현재 재작성 횟수 (재작성 시 참조) |

> `examiner_issues`와 `revision_count`는 examiner → claims 재시도 루프에서만 채워짐.
> 최초 실행 시에는 빈 list와 0.

---

## 출력 (반환 dict 키)

| 필드 | 타입 | 설명 |
|---|---|---|
| `claims` | `list[dict]` | 청구항 목록 (아래 구조 참조) |

### claims 항목 구조

```python
{
    "claim_number": int,        # 청구항 번호 (1부터 순서대로)
    "claim_type": str,          # "method" | "system" | "storage_medium"
    "is_independent": bool,     # True = 독립항, False = 종속항
    "depends_on": int,          # 독립항은 0, 종속항은 인용 항 번호
    "content": str,             # 청구항 전문
}
```

---

## 후속 노드

- **examiner** — `claims`를 심사

---

## 재시도 조건 (graph.py)

examiner가 `is_registerable = False`를 반환하고 `revision_count < MAX_REVISION(2)`이면 다시 실행.
재실행 시 `examiner_issues`를 참조해 지적된 청구항을 수정.

---

## 구현 시 주의사항

- 독립항은 반드시 방법(method), 시스템(system), 기록매체(storage_medium) 3종 포함
- 종속항은 독립항을 구체화하는 내용
- 청구항 전문은 한국 특허법 형식 준수: "~하는 방법", "~하는 시스템"
- 재작성 시 `revision_count`를 1 증가시켜 반환

```python
return {
    "claims": [...],
    "revision_count": state.get("revision_count", 0) + 1,
}
```

---

## 예시 반환값

```python
{
    "claims": [
        {
            "claim_number": 1,
            "claim_type": "method",
            "is_independent": True,
            "depends_on": 0,
            "content": "IoT 센서로 주차 공간의 점유 여부를 감지하는 단계; ...",
        },
        {
            "claim_number": 2,
            "claim_type": "system",
            "is_independent": True,
            "depends_on": 0,
            "content": "주차 공간에 설치된 IoT 센서; ...",
        },
        {
            "claim_number": 3,
            "claim_type": "method",
            "is_independent": False,
            "depends_on": 1,
            "content": "제1항에 있어서, AI 예측 모델로 빈자리 발생을 사전 예측하는 단계를 더 포함하는 방법.",
        },
    ]
}
```
