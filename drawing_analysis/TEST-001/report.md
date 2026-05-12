# 도면 생성 리포트 - TEST-001

- 생성일시: 2026-05-12 15:05:17
- 렌더러: 좌표 기반 특허청 스타일 SVG 직접 렌더러 v5
- 총 도면 수: 2
- 평균 품질 점수: 100.0
- 통과 기준: 75점 이상
- 통과/검토필요: 2/0

## 1. 도면별 요약

| 도면 | 제목 | 유형 | 품질점수 | 등급 | SVG | PNG | Layout |
|---|---|---|---:|---|---|---|---|
| 도 1 | 이미지 분류 시스템의 전체 구성도이다 | block_diagram | 100 | A | TEST-001_fig_1.svg | TEST-001_fig_1.png | TEST-001_fig_1_layout.json |
| 도 2 | 이미지 분류 방법의 처리 흐름도이다 | flowchart | 100 | A | TEST-001_fig_2.svg | TEST-001_fig_2.png | TEST-001_fig_2_layout.json |

## 2. 산출물 설명

| 파일 | 의미 |
|---|---|
| local_extraction.json | 정규식 기반 도면/부호 추출 결과 |
| patent_analysis.json | LLM 기반 전체 발명 분석 JSON |
| figures.json | 생성 대상 도면 목록 |
| *_fig_*.json | 도면별 설계 JSON |
| *_fig_*.svg | 좌표 기반 특허청 스타일 SVG 출력 |
| *_fig_*.png | SVG에서 변환된 PNG 출력 |
| *_fig_*_layout.json | 렌더링 레이아웃 메타데이터 |
| *_fig_*_validation.json | 구조/품질 검증 결과 |
| report.md | 본 리포트 |

## 3. 참고

- 본 버전은 Mermaid 자동배치를 사용하지 않고 SVG를 직접 생성합니다.
- 기계 단면도/사시도는 별도 CAD/이미지 생성 렌더러가 필요합니다.
- 현재 버전은 블록도/흐름도/시스템 구성도 실무 스타일에 최적화되어 있습니다.
