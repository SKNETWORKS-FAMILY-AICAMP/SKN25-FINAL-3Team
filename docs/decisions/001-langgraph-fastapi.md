# ADR 001 — LangGraph + FastAPI 채택

날짜: 2026-05
상태: 결정됨

---

## 맥락

특허 명세서 자동 생성 파이프라인을 구현하기 위해 에이전트 오케스트레이션 방식과 백엔드 구조를 결정해야 했습니다.

## 결정

**LangGraph** (에이전트 프레임워크) + **FastAPI** (API 서버) 조합을 채택합니다. (`docs/architecture.md` 옵션 B+B)

## 이유

### LangGraph 선택 이유
- 노드 간 조건부 분기(examiner → claims 재시도 루프)를 선언적으로 표현 가능
- `PatentAgentState`로 파이프라인 전체 상태를 한 곳에서 관리
- 병렬 실행(consulting → patent_search + claims 동시)을 엣지 구조로 자연스럽게 표현
- LangChain 생태계와 통합 용이 (langchain-openai, 메모리, 툴 호출)

### FastAPI 선택 이유
- async 처리로 LLM 호출 대기 중 다른 요청 처리 가능
- Pydantic 스키마로 에이전트 입출력 타입 안전성 보장
- Django와 독립적으로 에이전트 레이어를 확장 가능

## 결과

- 노드 함수 시그니처는 `def run(state: PatentAgentState) -> dict`로 고정
- State 변경은 팀 합의 사항 (`agents/state.py` 단독 수정 금지)
- 새 노드 추가 시 `graph.py`의 `add_node` + `add_edge` 동시 수정 필수

## 대안 (채택하지 않은 이유)

- **순수 Python 클래스**: 노드 간 상태 전달 및 조건부 루프를 직접 구현해야 해 복잡도 증가
- **Django 단일**: 비동기 LLM 호출 처리가 어렵고 에이전트 레이어 독립 확장 불가
