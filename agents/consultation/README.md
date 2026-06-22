# Consultation / Prior-Art Agents

상담 상태 관리, 상담 DB 저장, 선행기술조사 연동 코드가 있는 폴더입니다.

청구항 생성 구현은 `agents/claim/`로 분리했습니다. 이 폴더의 `claim_agent.py`는 예전 import가 깨지지 않게 둔 호환용 shim입니다.

## 현재 파일

```text
consultation_agent.py   상담 흐름, 발명 슬롯 추출, DB 저장
prior_art_agent.py      선행기술 후보 검색/분석
claim_agent.py          호환용 shim → agents/claim/claim_agent.py 재수출
patent_db.py            특허 corpus DB 연결
load_corpus.py          특허 TXT → DB 적재
agent_payloads.py       downstream agent용 payload 변환
document_utils.py       PDF/DOCX/HWP 추출 유틸
```

Streamlit 화면은 `apps/streamlit/main.py`에 둡니다.

## 데이터 위치

특허 TXT 원천 데이터는 이 폴더에 넣지 않습니다.

기본 위치:

```text
data/raw/texts/patents_txt/
```

적재 예시:

```bash
uv run python agents/consultation/load_corpus.py --dir data/raw/texts/patents_txt
```

다른 위치를 쓰고 싶으면 `.env`에 지정합니다.

```env
PATENTS_TEXT_DIR=/absolute/path/to/patents_txt
```

## 환경변수

공통 값은 저장소 루트 `.env`에서 읽습니다.

```text
SKN25-FINAL-3Team/.env
```

이 에이전트만 별도 설정이 필요하면 아래 파일로 덮어쓸 수 있습니다.

```text
agents/consultation/.env
```

두 파일 모두 Git에 올리지 않습니다.
