# 구조 메모

이 폴더는 청구항 초안을 작성하는 Claim Agent 영역이다. 표준 진입점은 `agent.py`, graph 연결은 `adapter.py`, 출력 계약은 `agents/schemas/claim.py`를 따른다.

---

# Claim Agent

청구항 생성/저장 관련 에이전트 코드 위치입니다.

- `claim_agent.py`: 상담 DB 내용을 청구항 생성 입력으로 변환하고 생성 청구항을 DB에 저장합니다.
- 서비스 화면에서는 `apps/streamlit/main.py`가 이 모듈을 호출합니다.

학습 노트북은 `notebooks/claim/`, 학습 JSONL은 `data/processed/claim_loop/training/`에 둡니다.