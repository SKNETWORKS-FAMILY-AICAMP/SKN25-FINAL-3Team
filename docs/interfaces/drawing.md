# Drawing Agent 인터페이스

> `agents/nodes/drawing.py` · `run(state)` 함수

---

## 역할

청구항 내용을 분석하여 특허 도면을 Mermaid.js 코드로 생성합니다.
흐름도(flowchart)와 시스템 구성도(system diagram) 2종을 생성합니다.

---

## 입력 (State 필드)

| 필드 | 타입 | 설명 |
|---|---|---|
| `claims` | `list[dict]` | 심사 완료된 청구항 목록 |

---

## 출력 (반환 dict 키)

| 필드 | 타입 | 설명 |
|---|---|---|
| `flowchart_code` | `str` | Mermaid.js 흐름도 코드 |
| `system_diagram_code` | `str` | Mermaid.js 시스템 구성도 코드 |

---

## 출력 예시

```python
{
    "flowchart_code": """
flowchart TD
    A[IoT 센서 감지] --> B{빈자리?}
    B -->|예| C[서버 업데이트]
    B -->|아니오| D[점유 상태 유지]
    C --> E[앱 알림 발송]
""",
    "system_diagram_code": """
graph LR
    Sensor[IoT 센서] --> Server[중앙 서버]
    Server --> App[모바일 앱]
    Server --> DB[(데이터베이스)]
""",
}
```

---

## 구현 시 주의사항

- Mermaid.js 문법 오류 없이 렌더링 가능한 코드 생성
- 흐름도는 method 청구항 기반, 시스템 구성도는 system 청구항 기반
- 특허 도면은 번호가 붙은 구성요소로 표현 (예: `A[1. IoT 센서]`)
