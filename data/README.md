# Data Folder

이 폴더는 특허 데이터 작업 공간입니다.

## 원칙

- 대량 PDF/TXT/SQLite/HTML 리포트는 Git에 올리지 않습니다.
- Git에 올리는 것은 manifest, 작은 샘플, 문서, 스크립트입니다.
- 원문 위치는 Google Drive/GCS URI로 manifest에 기록합니다.

## 구조

```text
data/
├─ manifests/                 # Drive/GCS 파일 목록, split manifest
├─ raw/
│  ├─ pdfs/                   # 원문 PDF 로컬 캐시
│  │  ├─ legacy-root/         # 예전 repo 루트에 있던 PDF 정리 위치
│  │  └─ g06f/latest10/       # 기존 latest10 G06F PDF 캐시
│  └─ texts/                  # 원문/추출 텍스트 캐시
├─ processed/
│  ├─ patent_structures/      # PDF/TXT → 구조화 정답 JSON
│  ├─ simulated_consultations/# 특허 구조 → 가상 상담내역
│  ├─ invention_payloads/     # 상담 에이전트 출력
│  └─ agent_payloads/         # 후속 에이전트별 payload
├─ reports/
│  ├─ extraction/             # 추출 품질 리포트
│  ├─ consultation/           # 상담 에이전트 품질 리포트
│  └─ evaluation/             # 검색/생성 평가 리포트
└─ tmp/                       # 임시 파일
```

## 현재 manifest

- `data/manifests/drive_inventory_2026-05-12.jsonl`
- `data/manifests/drive_inventory_2026-05-12.csv`
- `data/manifests/drive_inventory_2026-05-12.summary.json`

## 주의

`data/raw/`, `data/processed/`, `data/reports/`, `data/tmp/`의 대량 산출물은 `.gitignore`로 제외합니다.
