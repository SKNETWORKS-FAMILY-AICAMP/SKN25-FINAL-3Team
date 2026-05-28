# agents

이 폴더는 특허 명세서/청구항/도면 생성 파이프라인의 에이전트 계층을 담는다.

## 구조 원칙

- `graph.py`: 전체 실행 흐름을 연결한다.
- `state.py`: 모든 에이전트가 공유하는 상태 스키마를 정의한다.
- `schemas/`: 각 에이전트의 입출력 계약을 Pydantic 모델로 정의한다.
- `adapters/`: graph/state와 실제 agent 실행부 사이의 변환 계층이다.
- `master/`: 어떤 에이전트를 다음에 실행할지 결정하는 라우팅 계층이다.
- 개별 에이전트 폴더(`summary`, `claim`, `drawing` 등)는 자기 역할의 `agent.py`, `adapter.py`, `README.md`를 가진다.
