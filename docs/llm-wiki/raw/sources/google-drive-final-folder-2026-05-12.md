---
title: Google Drive Final Folder 2026-05-12
created: 2026-05-12
updated: 2026-05-12
type: source
tags: [source, data, patent]
sources: []
confidence: high
---

# Google Drive Final Folder 2026-05-12

## 출처

- Google Drive folder: <https://drive.google.com/drive/folders/1V-KJTNLjYpxqp_VAgIxKYQO6pm8-zMa2>
- 공유 폴더명: `final`
- 분석 방식: `gdown.download_folder(..., skip_download=True)`로 파일 목록만 수집
- 실제 대량 다운로드는 하지 않았습니다.

## 분석 결과

| 항목 | 개수 |
|---|---:|
| 전체 파일 | 1,998 |
| PDF | 779 |
| TXT | 1,219 |

## 상위 폴더별 파일 수

| 폴더 | 파일 수 | 해석 |
|---|---:|---|
| `심사관` | 914 | 심사관/추가 자료로 보이며 PDF와 추출 TXT가 섞여 있음 |
| `extracted_texts` | 542 | 원문 PDF에서 추출된 텍스트 묶음 |
| `G06Q` | 192 | G06Q 원문/추출 텍스트 |
| `G06N` | 143 | G06N 원문/추출 텍스트 |
| `G06F` | 110 | G06F 원문 PDF |
| `G06V` | 97 | G06V 원문/추출 텍스트 |

## IPC 폴더 기준 추정

| IPC 폴더 | 파일 수 |
|---|---:|
| G06Q | 384 |
| G06N | 286 |
| G06F | 220 |
| G06V | 194 |
| 없음/기타 | 914 |

## 생성된 manifest

- `data/manifests/drive_inventory_2026-05-12.jsonl`
- `data/manifests/drive_inventory_2026-05-12.csv`
- `data/manifests/drive_inventory_2026-05-12.summary.json`

각 row는 다음 정보를 가집니다.

```json
{
  "drive_file_id": "",
  "drive_path": "G06F/1020250193994.pdf",
  "file_name": "1020250193994.pdf",
  "extension": "pdf",
  "top_folder": "G06F",
  "ipc_folder": "G06F",
  "patent_id_guess": "1020250193994",
  "source_url": "https://drive.google.com/file/d/.../view"
}
```

## 현재 결정

- 전체 PDF를 바로 다운로드하지 않습니다.
- 우선 Drive 파일 목록을 manifest로 관리합니다.
- smoke set 20~30건만 로컬에 내려받아 파이프라인을 검증합니다.
- PDF 원문은 `data/raw/pdfs/` 아래 캐시로만 둡니다.
- TXT 원문/추출 텍스트는 `data/raw/texts/` 또는 `data/processed/`로 분리합니다.

## 관련 문서

- [[data-management-strategy]]
- [[pilot-600-v1]]
- [[pipeline-and-evaluation]]
