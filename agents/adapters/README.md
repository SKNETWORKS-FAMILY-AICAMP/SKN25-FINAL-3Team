# agents/adapters

이 폴더는 `graph.py`와 각 에이전트의 `agent.py` 사이를 연결하는 어댑터 계층이다.

## 역할

- state에서 해당 에이전트에 필요한 입력만 추출한다.
- agent/API 호출용 payload로 변환한다.
- agent 산출물을 schema로 검증한다.
- 검증된 결과를 다시 state에 저장 가능한 형태로 변환한다.

## 원칙

- graph는 agent.py를 직접 호출하지 않는다.
- graph는 adapter만 호출한다.
- adapter는 상세 비즈니스 로직을 가지지 않고 입출력 변환 책임만 가진다.
