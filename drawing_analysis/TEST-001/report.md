# 도면 생성 리포트 - TEST-001

- 생성일시: 2026-05-11 16:48:14
- 총 도면 수: 2
- 평균 품질 점수: 85.0
- 통과 기준: 75점 이상
- 통과/검토필요: 2/0

## 1. 도면별 요약

| 도면 | 제목 | 유형 | 품질점수 | 등급 | 자동수정 | MMD | SVG | PNG | Vision |
|---|---|---|---:|---|---:|---|---|---|---|
| 도 1 | 이미지 분류 시스템의 전체 구성도이다 | block_diagram | 85 | B | 1회 | TEST-001_fig_1.mmd | TEST-001_fig_1.svg | TEST-001_fig_1.png | - |
| 도 2 | 이미지 분류 방법의 처리 흐름도이다 | flowchart | 85 | B | 1회 | TEST-001_fig_2.mmd | TEST-001_fig_2.svg | TEST-001_fig_2.png | - |

## 2. 등급 기준

- A: 90점 이상, 바로 시연 가능 수준
- B: 75점 이상, 기본 품질 통과
- C: 60점 이상, 검토 후 사용 권장
- D: 60점 미만, 재생성 또는 수동 보완 필요

## 3. 산출물 설명

| 파일 | 의미 |
|---|---|
| local_extraction.json | 정규식 기반 도면/부호 추출 결과 |
| patent_analysis.json | LLM 기반 전체 발명 분석 JSON |
| figures.json | 생성 대상 도면 목록 |
| *_fig_*.json | 도면별 설계 JSON |
| *_fig_*.mmd | Mermaid 도면 코드 |
| *_fig_*.svg | Mermaid CLI 기반 SVG 출력 |
| *_fig_*.png | Mermaid CLI 기반 PNG 출력, Vision 검수 입력 |
| *_fig_*_validation.json | 구조/문법/품질 검증 결과 |
| *_fig_*_vision.json | Vision 기반 도면 검수 결과 |
| *_metadata.json | 전체 생성 메타데이터 |
| report.md | 본 리포트 |

## 4. 다음 검토 포인트

- 점수 75점 미만 도면은 fig_json의 elements/relations/source_text를 우선 확인하세요.
- 관계선이 없는 block_diagram은 명세서상 구성요소 간 데이터 흐름 문장을 추가 추출해야 합니다.
- Vision 결과에서 도면부호 누락 또는 연결선 혼동이 나오면 특허사 스타일 템플릿을 patent_office로 유지하세요.
