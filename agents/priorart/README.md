# 구조 메모

이 폴더는 선행기술 후보를 검색/평가하는 Prior Art Agent 영역이다. 표준 진입점은 `agent.py`, graph 연결은 `adapter.py`, 출력 계약은 `agents/schemas/prior_art.py`를 따른다.

---

# Prior Art Agent

## 역할
- 특허 TXT 코퍼스 로드
- 임베딩 기반 유사 선행문헌 검색
- 후보별 겹치는 점, 차이점, 종래기술 한계, 리스크 분석