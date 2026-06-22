---
title: Pilot 600 v1
created: 2026-05-12
updated: 2026-05-12
type: concept
tags: [data, patent, evaluation]
sources: [raw/sources/google-drive-final-folder-2026-05-12.md]
confidence: medium
---

# Pilot 600 v1

## 한 줄 요약

`pilot_600_v1`은 AI/소프트웨어 특허 상담 에이전트를 개발하기 위한 대표 샘플 데이터셋입니다.

## 목적

이 데이터셋은 최종 서비스 입력이 아닙니다.  
기존 특허 PDF/TXT를 이용해 구조화 JSON과 가상 상담내역 JSON을 만들기 위한 개발용 기준 자료입니다.

```text
특허 PDF/TXT
→ patent_structure JSON
→ simulated_consultation JSON
→ invention_payload 품질 확인
```

## 원천

- Google Drive 폴더: [[google-drive-final-folder-2026-05-12]]
- 현재 Drive inventory: 1,998 files
- PDF: 779개
- TXT: 1,219개

## split 기준

아직 최종 확정은 아닙니다.

| split | 권장 수량 | 용도 |
|---|---:|---|
| smoke | 20~30 | 코드가 돌아가는지 빠르게 확인 |
| dev | 300~400 | 추출/상담/검색 로직 개발 |
| validation | 100~150 | 품질 비교, 파라미터 조정 |
| test | 50~100 | 최종 보고용 고정 평가 |
| holdout | 선택 | 과적합 확인 |

## 샘플링 기준

단순 랜덤이 아니라 아래 축을 골고루 섞습니다.

| 축 | 예시 |
|---|---|
| IPC | G06F, G06N, G06V, G06Q, G16C |
| 문제 유형 | 예측, 분류, 추천, 최적화, 이상탐지, 자동화, 생성 |
| 해결 유형 | 모델 학습, 추론, 데이터 전처리, UI, 시스템 아키텍처 |
| 청구항 유형 | 방법, 장치, 시스템, 기록매체, 프로그램 |
| 문서 품질 | 섹션 명확, OCR 어려움, 도면 의존도 높음 |

## manifest 필드

manifest는 데이터 파일 목록표입니다. 상세 설명은 [[data-management-strategy]]의 `manifest란?` 섹션을 봅니다.

현재는 실제 JSON 예시를 문서에 길게 적지 않고, 필요한 필드 후보만 관리합니다.

초기 필드 후보:

- dataset_id
- subset_id
- patent_id
- source
- drive_file_id
- drive_path
- source_url
- local_pdf_path
- ipc_codes
- sample_reason
- status
- split
- notes

## 상태값 후보

| status | 의미 |
|---|---|
| not_downloaded | Drive 목록에만 있음 |
| downloaded | 로컬 PDF 캐시 있음 |
| text_available | 추출 TXT 있음 |
| structure_extracted | `patent_structure` 생성 완료 |
| consultation_generated | 가상 상담내역 생성 완료 |
| evaluated | 상담/검색 평가 완료 |
| failed | 처리 실패 |
| excluded | 제외 대상 |

## 오늘 기준 결정

- 전체 PDF를 한 번에 받지 않습니다.
- Drive 목록은 `data/manifests/drive_inventory_2026-05-12.*`에 저장했습니다.
- `smoke_g06f_latest10` 10건 manifest를 만들고 PDF만 로컬 캐시했습니다.
- 다음 단계는 G06N/G06V/G06Q까지 포함한 smoke 30건으로 확장하는 것입니다.

## 관련 문서

- [[data-management-strategy]]
- [[patent-data-schemas]]
- [[pipeline-and-evaluation]]
