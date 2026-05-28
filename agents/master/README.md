# agents/master

이 폴더는 전체 파이프라인에서 다음 실행 대상을 결정하는 Master/Router 계층이다.

## 역할

- 현재 state를 보고 다음 에이전트를 결정한다.
- 입력 부족 시 consultation으로 보낸다.
- 산출물 누락 시 해당 에이전트로 보낸다.
- 나중에 LLM 기반 Master로 교체하더라도 반환 스키마는 유지한다.
