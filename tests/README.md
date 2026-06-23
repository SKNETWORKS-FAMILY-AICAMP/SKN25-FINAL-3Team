# Pytest 단위 테스트 안내

현재 저장소의 실제 Python 구조를 기준으로 재작성한 테스트 모음입니다. 과거의
`agents.state`, `agents.graph`, `backend.fastapi.app.*` 구조는 사용하지 않습니다.

## 실행

저장소 루트에서 다음 명령을 실행합니다.

```bash
.venv/bin/python -m pytest tests
```

간결한 결과만 보려면 다음 명령을 사용합니다.

```bash
.venv/bin/python -m pytest tests -q
```

## 구성

### `tests/agents`

- `test_state.py`: Pydantic 상태·청구항·도면·선행기술 스키마 계약
- `test_graph.py`: 전체 특허 LangGraph의 승인·보정·종료 분기
- `test_claim_review_graph.py`: 심사·보정 전용 그래프의 반복 흐름
- `test_examiner.py`: 심사 결과 JSON 복구, revision 증가, 실패 fallback
- `test_agent_units.py`: Summary, Claim, Rewrite, Paper Analyzer, Drawing 에이전트
- `test_prior_art.py`: 청구항 검색문 추출, 리스크 집계, 중복 병합
- `test_specification_helpers.py`: 명세서 JSON 파싱, 재료 수집, 검증 헬퍼

### `tests/api`

- `test_claim_review.py`: 청구항 텍스트 파싱과 심사 NDJSON 스트림
- `test_claims_worker.py`: 청구항 생성·선행기술 결과 스트림
- `test_workers.py`: FastAPI route 등록, 도면·명세서·특허 검색 worker
- `test_claim_review_auth.py`: Django 심사 프록시의 JWT 인증 경계

### `tests/django`

- `test_accounts.py`: 표준 User, UserProfile, signup/login/me/logout API
- `test_workspace.py`: 프로젝트·입력·상담·청구항·도면·보고서 모델 관계
- `test_workspace_views.py`: 프로젝트·청구항 저장, 파일 추출, Markdown 변환

## 격리 원칙

- OpenAI, RunPod, LangSmith, S3, KIPRIS, PostgreSQL을 실제 호출하지 않습니다.
- Django 검증은 임시 SQLite DB를 사용하며 실행 후 삭제합니다.
- LLM·검색·스토리지 결과는 각 테스트에서 명시적으로 대체합니다.
- `pytest-django`, `pytest-mock` 없이 표준 fixture와 `unittest.mock` 호환 방식으로 실행됩니다.
- `xmltodict`가 누락된 오래된 로컬 가상환경에서는 테스트 전용 표준 라이브러리
  fallback을 사용합니다. 정상적으로 동기화된 환경에서는 프로젝트에 선언된 실제
  `xmltodict` 패키지를 사용합니다.

## 최종 검증 결과

- 실행일: 2026-06-22
- 결과: **108 passed, 9 warnings in 6.05s**
- 통과율: **108/108 (100%)**
- 경고: FastAPI/Starlette/LangSmith/PyMuPDF 계열의 서드파티 deprecation 경고
