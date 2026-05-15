# LLM Wiki

이 폴더는 AI/소프트웨어 특허 상담 프로젝트의 **팀 지식베이스**입니다.

처음 보는 팀원은 아래 순서로 읽으면 됩니다.

1. [`index.md`](index.md) — 전체 목차
2. [`concepts/llm-wiki-beginner-guide.md`](concepts/llm-wiki-beginner-guide.md) — LLM Wiki 초심자 설명
3. [`concepts/developer-workflow-scenario.md`](concepts/developer-workflow-scenario.md) — 개발 전/중/후에 Wiki를 어떻게 쓰는지 시나리오
4. [`concepts/team-collaboration-guide.md`](concepts/team-collaboration-guide.md) — 협업 규칙
5. [`concepts/data-management-strategy.md`](concepts/data-management-strategy.md) — 데이터 관리 전략
6. [`concepts/pipeline-and-evaluation.md`](concepts/pipeline-and-evaluation.md) — 예정 파이프라인과 다음 작업
7. [`SCHEMA.md`](SCHEMA.md) — 문서 작성 규칙, 문서 수정할 때 참고

## 핵심 요약

- 지금은 실제 사용자 상담 데이터를 확보하기 어렵기 때문에 **가상 상담내역**으로 개발합니다.
- 가상 상담내역은 특허 PDF/TXT를 보고 만들되, 실제 상담처럼 보이도록 변환합니다.
- PDF 원문은 Git에 넣지 않고 Drive/GCS + manifest로 관리합니다.
- LLM Wiki에는 데이터셋, 스키마 초안, 예정 파이프라인, 설계 메모, 의사결정을 남깁니다.
- 아직 개발 초기이므로 확정되지 않은 JSON 예시는 문서에 길게 고정하지 않습니다.

## 현재 Drive 분석 결과

공유한 Drive 폴더를 파일 목록만 분석했습니다.

- 전체 파일: 1,998개
- PDF: 779개
- TXT: 1,219개
- 상세: [`raw/sources/google-drive-final-folder-2026-05-12.md`](raw/sources/google-drive-final-folder-2026-05-12.md)

## 현재 데이터/프로젝트 폴더

자세한 전체 구조는 repo 루트의 [`docs/PROJECT_STRUCTURE.md`](../PROJECT_STRUCTURE.md)를 봅니다.

```text
agents/consultation/          # 상담 상태, 상담 DB, 선행기술 연동
agents/claim/                 # 청구항 생성/저장 코드
agents/drawing/               # 도면 생성 코드
apps/streamlit/               # Streamlit 데모 앱
notebooks/claim/              # 청구항 실험 노트북
models/claim/                 # 모델 설정/adapter 위치, 가중치는 Git 제외
docs/llm-wiki/schemas/        # 스키마/추출 기준 문서
data/
├─ manifests/                 # Drive 파일 목록, split manifest
├─ raw/                       # 원문 PDF/TXT 캐시, Git 제외
├─ processed/                 # 구조화 JSON, 가상 상담내역, claim_loop/training
├─ reports/                   # 품질 리포트, Git 제외
└─ tmp/                       # 임시 파일, Git 제외
```

## 다음 작업

1. `pilot_600_v1.jsonl` 만들기
2. smoke 20~30건 선정
3. smoke PDF/TXT만 다운로드
4. PDF/TXT → `patent_structure` JSON 생성
5. `patent_structure` → `simulated_consultation` JSON 생성
6. 상담 에이전트 품질 리포트 작성
