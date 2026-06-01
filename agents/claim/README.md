# Claim Agent

청구항 agent는 서비스 graph에서 `agents.claim.adapter.ClaimAdapter`를 통해 호출합니다.

현재 기준:

- 입력: `summary`, `prior_art` 등 shared state
- 출력: `agents.schemas.claim.ClaimAgentOutput`
- 연결: `API → Master Router → Graph → ClaimAdapter → ClaimAgentOutput`

레거시 상담 DB/Streamlit/학습 노트북 흐름은 main 서비스 구조에서 제거했습니다.
실제 청구항 품질화 로직은 `ClaimAdapter.call_agent()` 또는 `run_claim_agent()` 내부에 schema 기반으로 연결합니다.
