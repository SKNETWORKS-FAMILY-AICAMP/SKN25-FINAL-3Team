# Description Agent 인터페이스

> `agents/nodes/description.py` · `run(state)` 함수

---

## 역할

컨설팅 결과와 도면을 바탕으로 특허 명세서 본문을 작성합니다.
한국 특허청 명세서 작성 형식에 맞게 각 섹션을 생성합니다.

---

## 입력 (State 필드)

| 필드 | 타입 | 설명 |
|---|---|---|
| `invention_flow` | `str` | 발명의 전체 흐름 |
| `problem` | `str` | 기존 발명의 문제점 |
| `differentiation` | `str` | 기존 발명과의 차별점 |
| `effect` | `str` | 발명의 효과 |
| `flowchart_code` | `str` | Mermaid 흐름도 코드 |
| `system_diagram_code` | `str` | Mermaid 시스템 구성도 코드 |
| `claims` | `list[dict]` | 최종 청구항 목록 |

---

## 출력 (반환 dict 키)

| 필드 | 타입 | 설명 |
|---|---|---|
| `background` | `str` | 배경기술 (발명의 배경이 되는 종래 기술) |
| `problem_statement` | `str` | 발명이 해결하려는 과제 |
| `solution` | `str` | 과제의 해결수단 |
| `drawing_description` | `str` | 도면의 간단한 설명 |
| `detailed_description` | `str` | 발명을 실시하기 위한 구체적인 내용 (실시예) |

---

## 구현 시 주의사항

- 한국 특허법 제42조 명세서 기재 요건 준수
- `detailed_description`은 청구항의 모든 구성요소를 설명해야 기재불비 방지
- 도면 설명에서 Mermaid 코드의 노드 ID를 참조 번호로 변환
- 각 필드는 최소 200자 이상 권장
