# 특허 코퍼스 적재 가이드

선행기술 검색(Prior Art Agent)에 사용하는 특허 벡터 DB를 구축하는 방법입니다.
최초 1회 또는 코퍼스를 갱신할 때 실행합니다.

---

## 구조 개요

```
S3 (KIPRIS XML)
  └── agents/priorart/load_corpus.py
        ├── xml_parser.py       — KIPRIS XML → dict 파싱
        ├── prior_art_agent.py  — OpenAI 임베딩 (text-embedding-3-small, 1536-dim)
        └── patent_db.py        — PostgreSQL patent_corpus 테이블 저장
```

`patent_corpus` 테이블 주요 컬럼:

| 컬럼 | 내용 |
|------|------|
| `application_number` | 출원번호 (중복 적재 방지 키) |
| `title` | 발명 명칭 |
| `abstract` | 요약 |
| `claim1` | 독립 청구항 1항 |
| `ipc_codes` | IPC 코드 목록 (JSON) |
| `examiner_cited` | 심사관 인용 선행문헌 (정확도 검증용) |
| `embedding` | 1536-dim 벡터 (pgvector, cosine 검색용) |

---

## 사전 준비

`.env`에 아래 항목을 추가합니다:

```dotenv
# 특허 코퍼스 적재 전용
RDS_DATABASE_URL=postgresql://patent:patent_pw@localhost:5432/patent_ai
S3_BUCKET=your-bucket-name
S3_PREFIX=kipris/raw/bibliography_xml/   # 기본값, 변경 불필요
```

> `RDS_DATABASE_URL`은 코퍼스 적재 스크립트 전용입니다.
> Docker Compose에서 FastAPI가 사용하는 `DATABASE_URL`과 **별도**로 설정해야 합니다.

AWS 자격증명도 필요합니다 (`~/.aws/credentials` 또는 환경변수):

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=ap-northeast-2
```

---

## 실행

### Docker Compose 환경에서

```bash
docker compose run --rm fastapi \
  python agents/priorart/load_corpus.py
```

버킷/프리픽스를 직접 지정하는 경우:

```bash
docker compose run --rm fastapi \
  python agents/priorart/load_corpus.py \
  --bucket your-bucket-name \
  --prefix kipris/raw/bibliography_xml/
```

### 로컬 환경에서

```bash
uv run python agents/priorart/load_corpus.py
```

### 옵션

| 옵션 | 설명 |
|------|------|
| `--bucket` | S3 버킷 이름 (기본값: `.env`의 `S3_BUCKET`) |
| `--prefix` | S3 키 프리픽스 (기본값: `kipris/raw/bibliography_xml/`) |
| `--reset` | 기존 데이터를 모두 삭제하고 재적재 |

---

## 동작 방식

1. S3에서 `.xml` 파일 목록을 수집하고 10개씩 병렬 다운로드합니다.
2. KIPRIS XML을 파싱해 출원번호·제목·요약·청구항 1항·IPC 코드를 추출합니다.
3. 이미 DB에 있는 출원번호는 건너뜁니다 (멱등 실행 가능).
4. 50건씩 배치로 OpenAI 임베딩을 호출하고 PostgreSQL에 저장합니다.

---

## 적재 확인

```bash
# Docker Compose 환경
docker compose exec postgres psql -U patent -d patent_ai \
  -c "SELECT COUNT(*) FROM patent_corpus;"

# 로컬
psql -U patent -d patent_ai -c "SELECT COUNT(*) FROM patent_corpus;"
```

벡터 인덱스(IVFFlat) 상태 확인:

```bash
psql -U patent -d patent_ai \
  -c "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'patent_corpus';"
```
