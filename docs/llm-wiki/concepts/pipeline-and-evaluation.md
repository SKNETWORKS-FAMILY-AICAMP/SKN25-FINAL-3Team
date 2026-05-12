---
title: Pipeline and Evaluation
created: 2026-05-12
updated: 2026-05-12
type: guide
tags: [pipeline, evaluation, data, patent]
sources: [raw/sources/google-drive-final-folder-2026-05-12.md]
confidence: medium
---

# Pipeline and Evaluation

## 한 줄 요약

현재 문서는 확정 파이프라인이 아니라, smoke set으로 데이터 생성과 상담 에이전트 품질을 검증하기 위한 **개발 초안**입니다.

## 전체 파이프라인 (예정, 현재 구현 안됨)

```text
1. Drive inventory 생성
2. pilot_600_v1 manifest 생성
3. smoke set 20~30건 선정
4. PDF/TXT 로컬 캐시 준비
5. PDF/TXT → patent_structure JSON 생성
6. patent_structure → simulated_consultation JSON 생성
7. simulated_consultation → 상담 에이전트 입력
8. invention_payload 생성
9. 사람이 품질 확인
10. 후속 에이전트로 확장 검토
```

주의:

- 위 흐름은 현재 가정입니다.
- 구현하면서 순서와 스키마가 바뀔 수 있습니다.
- 평가 기준은 아직 확정하지 않았습니다.

## 폴더별 역할

| 경로 | 역할 | Git 포함 여부 |
|---|---|---|
| `data/manifests/` | Drive 목록, split, 샘플 목록 | 포함 가능 |
| `data/raw/pdfs/` | 원문 PDF 로컬 캐시 | 원칙적으로 제외 |
| `data/raw/texts/` | 원문/추출 TXT 캐시 | 원칙적으로 제외 |
| `data/processed/patent_structures/` | PDF/TXT 기반 구조화 JSON | 대량은 제외 |
| `data/processed/simulated_consultations/` | 가상 상담내역 JSON | 대량은 제외 |
| `data/reports/` | 품질 리포트 | 대량/실험물 제외 |
| `docs/llm-wiki/` | 팀 지식베이스 | 포함 |

## 1단계: Drive inventory

이미 완료된 파일:

- `data/manifests/drive_inventory_2026-05-12.jsonl`
- `data/manifests/drive_inventory_2026-05-12.csv`
- `data/manifests/drive_inventory_2026-05-12.summary.json`

재생성 스크립트:

```bash
uv run --with gdown python scripts/data/build_drive_inventory.py
```

## 2단계: smoke set 선정

현재 생성된 smoke manifest:

- `data/manifests/pilot_600_v1_smoke_g06f_latest10.jsonl`
- 기준: G06F PDF 중 `patent_id_guess` 내림차순 최신 10건
- 로컬 캐시: `data/raw/pdfs/g06f/latest10/`

다운로드 재실행:

```bash
uv run --with gdown python scripts/data/download_smoke_pdfs.py \
  --manifest data/manifests/pilot_600_v1_smoke_g06f_latest10.jsonl
```

추가 smoke set 추천 기준:

- 최신 연도 위주 10건
- G06F/G06N/G06V/G06Q 균형 10건
- PDF와 TXT가 모두 있는 문서 우선 10건
- 너무 오래된 문서는 regression 용도로만 사용

## 3단계: PDF/TXT 구조화 JSON 생성

목표:

```text
PDF/TXT → data/processed/patent_structures/{patent_id}.json
```

아직 상세 필드는 확정하지 않습니다. 우선 JSON 파일이 생성되고, 원천 파일과 연결되며, 사람이 읽고 검토할 수 있으면 됩니다.

## 4단계: 가상 상담내역 JSON 생성

목표:

```text
patent_structure → data/processed/simulated_consultations/{consultation_id}.json
```

주의:

- 원문 명세서 문장을 그대로 복붙하지 않습니다.
- 사용자가 상담에서 말할 법한 표현으로 변환합니다.
- 일부 정보는 의도적으로 빠뜨려서 상담 에이전트가 후속 질문을 하게 만들 수 있습니다.

## 5단계: 상담 에이전트 평가

`simulated_consultation`을 입력으로 넣고 `invention_payload`를 생성합니다.

평가 기준은 아직 확정하지 않습니다. 우선 사람이 볼 수 있는 리포트를 만들고, 어떤 기준으로 봐야 할지 정리합니다.

후보 평가 축:

- 문제 이해
- 해결수단 이해
- 차별성 추출
- 효과 추출
- 알고리즘/구성요소 추출
- 부족정보 질문 품질
- 원천 근거 추적 가능성

## 6단계: 다음 작업 체크리스트

- [ ] `pilot_600_v1.jsonl` 생성
- [ ] smoke 30건 선정
- [ ] Drive에서 smoke PDF/TXT만 다운로드
- [ ] `patent_structure` JSON 생성 스크립트 작성
- [ ] `simulated_consultation` JSON 생성 스크립트 작성
- [ ] 상담 에이전트에 넣고 품질 리포트 생성
- [ ] LangGraph/LangChain 기반 상담 state 흐름 정리

## 관련 문서

- [[google-drive-final-folder-2026-05-12]]
- [[data-management-strategy]]
- [[pilot-600-v1]]
- [[patent-data-schemas]]
- [[agent-architecture-notes]]
