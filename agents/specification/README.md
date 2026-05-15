# Specification Agent

발명의 설명, 명세서 항목, DOCX 생성 관련 코드를 둡니다.

- `specification_agent.py`: 상담/청구항/도면 데이터를 바탕으로 발명의 설명 항목 생성 및 DB 저장
- `patent_docx.py`: 생성된 명세서/청구항/도면 데이터를 DOCX로 조립

상담 상태/DB 기본 모델은 `agents/consultation/`, 청구항은 `agents/claim/`, 도면 생성과 도면 DB는 `agents/drawing/`을 참조합니다.
