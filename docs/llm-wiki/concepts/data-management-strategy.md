---
title: Data Management Strategy
created: 2026-05-12
updated: 2026-05-15
type: concept
tags: [data, patent, consultation]
sources: [raw/sources/google-drive-final-folder-2026-05-12.md]
confidence: medium
---

# Data Management Strategy

## 한 줄 요약

현재 개발 데이터는 **특허 PDF에서 만든 기준 데이터**와 **가상 상담내역**을 중심으로 관리합니다. 실제 사용자 상담 데이터는 당장 확보하기 어렵기 때문에, 문서에서는 미래 가능성으로만 분리해서 다룹니다.

## 왜 필요한가

최종 서비스에서 사용자가 남기는 데이터는 PDF가 아니라 상담내역입니다.  
하지만 지금 개발 중에는 기존 특허 PDF를 보고 상담 상황을 역으로 만들어야 합니다.

둘을 섞으면 문제가 생깁니다.

- 에이전트가 상담 입력이 아니라 특허 문서 스타일에 과적합됨
- PDF 원문을 서비스 입력처럼 착각함
- 평가 기준이 불명확해짐
- 대량 PDF를 Git에 넣는 실수가 생김

## 데이터 계층

| 계층 | 이름 | 의미 | 저장 위치 | 현재 상태 |
|---|---|---|---|---|
| A | raw_reference_patents | 원문 특허 PDF/TXT | `data/raw/` 또는 Drive/GCS | Drive inventory 있음 |
| B | patent_structures | PDF/TXT에서 추출한 구조화 JSON | `data/processed/patent_structures/` | 초안 필요 |
| C | simulated_consultations | 특허 내용을 보고 만든 가상 상담내역 JSON | `data/processed/simulated_consultations/` | 초안 필요 |
| D | invention_payloads | 상담 에이전트가 만든 canonical payload | `data/processed/invention_payloads/` | 기존 코드와 연결 |
| E | real_user_consultations | 실제 사용자가 남길 수 있는 상담내역 | DB/비공개 저장소 | 현재 확보 어려움, Git 금지 |

## 현재 개발 흐름

아직 확정 파이프라인이 아니라 개발 초안입니다.

```text
특허 PDF/TXT
→ patent_structure JSON 초안 생성
→ simulated_consultation JSON 생성
→ 상담 에이전트가 invention_payload 생성
→ 사람이 품질 확인
```

## Git에 넣는 것 / 안 넣는 것

### Git에 넣는 것

- LLM Wiki 문서
- 작은 manifest CSV/JSONL
- 데이터 처리 스크립트
- 스키마 초안 문서
- 작은 샘플 JSON이 꼭 필요할 때만 최소 예시

### Git에 넣지 않는 것

- 대량 PDF
- 대량 추출 TXT
- SQLite DB
- HTML 실험 리포트
- 개인정보 또는 실제 상담내역
- `.env`

## 로컬 폴더 규칙

전체 프로젝트 폴더 구조는 repo 루트의 `docs/PROJECT_STRUCTURE.md`를 기준으로 봅니다.

데이터 쪽 현재 규칙:

```text
data/
├─ manifests/                 # Drive/GCS 파일 목록, 샘플 split
├─ raw/
│  ├─ pdfs/                   # 원문 PDF 캐시, Git 제외
│  └─ texts/                  # 원문/추출 TXT 캐시, Git 제외
├─ processed/
│  ├─ patent_structures/      # PDF/TXT → 구조화 JSON
│  ├─ simulated_consultations/# 가상 상담내역 JSON
│  ├─ invention_payloads/     # 상담 에이전트 출력
│  ├─ agent_payloads/         # 후속 에이전트별 입력
│  ├─ claim_loop/training/    # 청구항 학습용 작은 JSONL
│  └─ examples/               # 작은 예시 JSON
├─ reports/                   # 사람이 보는 품질 리포트, Git 제외
└─ tmp/                       # 임시 파일, Git 제외
```

청구항/도면/앱/모델 쪽 현재 규칙:

```text
agents/consultation/          # 상담 상태, 상담 DB, 선행기술 연동
agents/claim/                 # 청구항 생성/저장 코드
agents/drawing/               # 도면 생성 코드
agents/specification/         # 발명의 설명/명세서/DOCX 생성 코드
apps/streamlit/               # Streamlit 데모 앱
notebooks/claim/              # 청구항 실험 노트북
models/claim/                 # 모델 설정/adapter 위치, 가중치는 Git 제외
docs/llm-wiki/schemas/        # 스키마/추출 기준 문서
```

## manifest란?

manifest는 **데이터 파일 목록표**입니다.

그냥 JSON 하나라기보다는, 보통 `JSONL` 또는 `CSV`로 관리하는 “어떤 파일이 어디에 있고 어떤 샘플인지 적어둔 장부”에 가깝습니다.

예:

```text
특허번호 | Drive 파일 ID | IPC | 로컬 PDF 경로 | split | 상태
```

왜 쓰는지:

- PDF를 전부 다운로드하지 않아도 전체 목록을 관리할 수 있음
- 어떤 파일을 smoke/test/train에 썼는지 추적 가능
- 팀원이 같은 샘플을 다시 받을 수 있음
- Git에는 작은 manifest만 올리고, 대용량 PDF는 Drive/GCS에 둘 수 있음

현재 manifest:

- `data/manifests/drive_inventory_2026-05-12.jsonl`
- `data/manifests/drive_inventory_2026-05-12.csv`
- `data/manifests/pilot_600_v1_smoke_g06f_latest10.jsonl`

## 현재 결정

- 공유 Drive 폴더는 [[google-drive-final-folder-2026-05-12]]에 기록했습니다.
- Drive에는 PDF 779개와 TXT 1,219개가 있습니다.
- 전체를 다운로드하지 않고 `data/manifests/drive_inventory_2026-05-12.*`로 먼저 관리합니다.
- 기존 루트 PDF는 `data/raw/pdfs/legacy-root/`로 정리합니다.
- 루트/한글 `청구항/`/`agents/consultation/`에 섞여 있던 청구항·도면·명세서·앱·스키마 파일은 `agents/claim/`, `agents/drawing/`, `agents/specification/`, `apps/streamlit/`, `notebooks/claim/`, `data/processed/claim_loop/training/`, `models/claim/`, `docs/llm-wiki/schemas/`로 분리합니다.
- 실제 사용자 상담 데이터는 현재 확보하기 어렵기 때문에, 당장은 `simulated_consultation` 중심으로 개발합니다.

## 다음 작업

1. `pilot_600_v1` manifest를 확정합니다.
2. smoke set 20~30건을 고릅니다.
3. PDF/TXT pair가 있는 문서를 우선 처리합니다.
4. `patent_structure` JSON 생성 스크립트를 만듭니다.
5. `simulated_consultation` 생성 규칙을 만듭니다.
6. 사람이 품질 검토할 기준은 별도로 정합니다.

## 관련 문서

- [[pilot-600-v1]]
- [[patent-data-schemas]]
- [[pipeline-and-evaluation]]
- [[team-collaboration-guide]]
- [[llm-wiki-beginner-guide]]
