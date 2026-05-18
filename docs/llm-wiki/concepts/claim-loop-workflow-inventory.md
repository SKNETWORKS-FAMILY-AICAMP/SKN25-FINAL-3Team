---
title: Claim Loop Workflow Inventory
created: 2026-05-15
updated: 2026-05-15
type: concept
tags: [patent, pipeline, evaluation, data]
sources: []
confidence: high
---

# Claim Loop Workflow Inventory

## 한 줄 요약

전날 청구항 loop 작업은 `hw` 브랜치에서 진행된 것으로 세션 기록과 현재 repo 상태가 일치한다. 핵심 흐름은 PDF에서 청구항 구조를 rule로 뽑고, 청구항을 가린 public payload로 GPT가 청구항을 생성한 뒤, answer key/evaluator/human review로 프롬프트와 입력 context를 고치는 loop다.

관련 문서: [[data-management-strategy]], [[pipeline-and-evaluation]], [[developer-workflow-scenario]], [[patent-data-schemas]]

## 브랜치

| 항목 | 값 | 근거 |
|---|---|---|
| 전날 세션 기록 브랜치 | `hw` | session search 요약에 `BRANCH=hw` 기록 |
| 현재 확인한 브랜치 | `hw` | `git branch --show-current` |
| 참고 원격 브랜치 | `origin/claim` | 청구항 관련 과거 PR/merge 흔적은 있으나, 전날 loop 작업 세션 기준은 `hw` |

주의: 현재 PR/정리 작업으로 파일 위치가 일부 바뀌었기 때문에, 최종 기준은 현재 `hw` 브랜치의 경로를 따른다.

## 코드 파일

| 파일 | 역할 | 비고 |
|---|---|---|
| `scripts/analysis/claim_loop_dataset.py` | PDF에서 청구항 구조 추출, dev/test split, public/answer_key JSONL 생성 | A/B/C rule 중 C structured rule checker 기준 |
| `scripts/analysis/claim_loop_run.py` | 생성/평가 loop 실행 | `dry-run`, `generate`, `evaluate-dry-run`, `evaluate` 모드 |
| `scripts/analysis/claim_graph_workflow.py` | public context → brief → invention graph → claim plan → generated claims → eval | graph 기반 4건 cohort 실험 |
| `scripts/analysis/claim_skeleton_workflow.py` | public context → brief/internal prior art → relation router/graph → claim skeleton → generated claims → eval | claim skeleton과 complexity/claim count control 실험 |
| `scripts/analysis/claim_workflow_mvp.py` | 단일/초기 MVP claim workflow 실험 | 2025 포장 최적화 케이스 등 초기 검증용 |

## 데이터셋 산출물

### v3 claim_end/category fix 전체 데이터셋

| 파일 | 줄 수 | 역할 |
|---|---:|---|
| `data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_claim_structure.jsonl` | 43 | 43개 PDF 전체 청구항 구조. `claims`, `claim_stats`, `sections` 포함 |
| `data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_claim_generation_dev.jsonl` | 10 | dev용. reference claims 포함, rule/prompt 설계용 |
| `data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_claim_generation_test_public.jsonl` | 33 | test input. 청구항 제거, 발명 설명 context만 포함 |
| `data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_claim_generation_test_answer_key.jsonl` | 33 | test 평가용 원본 청구항 answer key |

요약 통계:

```text
처리 성공 PDF: 43건
총 청구항: 758
독립항: 140
종속항: 478
삭제항: 140
dev: 10건
test: 33건
```

### cohort4 clean 생성/평가용 데이터셋

| 파일 | 줄 수 | 역할 |
|---|---:|---|
| `data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_cohort4_public.jsonl` | 4 | old/middle/recent/latest 4건 생성 입력 |
| `data/processed/claim_loop/g06f_claim_loop_v3_claim_end_category_fix_cohort4_answer_key.jsonl` | 4 | cohort4 평가용 원본 청구항 |

대상:

```text
1020080137371 2008
1020157028995 2015
1020200015713 2020
1020250193994 2025
```

### skeleton test5 데이터셋

| 파일 | 줄 수 | 역할 |
|---|---:|---|
| `data/processed/claim_loop/g06f_claim_loop_v3_skeleton_test5_public.jsonl` | 5 | claim skeleton workflow 입력 |
| `data/processed/claim_loop/g06f_claim_loop_v3_skeleton_test5_answer_key.jsonl` | 5 | skeleton workflow 평가용 원본 청구항 |

## Markdown / 보고서 산출물

### 핵심 handoff / 설계 문서

| 파일 | 역할 |
|---|---|
| `data/reports/pdf_analysis/session_handoff_claim_workflow_2026-05-14.md` | 전날 claim graph/skeleton 실험 전체 handoff. 비용, 실패/성과, 다음 방향 정리 |
| `data/reports/pdf_analysis/g06f_claim_loop_problem_strategy_v0.md` | claim loop 문제정의, human review 필요성, 평가표 v0, category 설계 방향 |
| `data/reports/pdf_analysis/problem3_final_judgement_claim_loop.md` | 독립항이 많이 잡히는 문제에 대한 최종 판단. rule+LLM+human 조합 필요 |
| `data/reports/pdf_analysis/g06f_claim_structure_smoke.md` | 5건 smoke 청구항 구조 분석 |
| `data/reports/pdf_analysis/g06f_10_claim_loop_methods.md` | 10건, 3가지 추출 방식 A/B/C 비교 |
| `data/reports/pdf_analysis/generalization_audit_graph_workflow.md` | graph workflow 일반화/오버피팅 점검 |

### 데이터셋/리뷰팩 문서

| 파일 | 역할 |
|---|---|
| `data/reports/pdf_analysis/g06f_claim_loop_v3_claim_end_category_fix_claim_loop_dataset_report.md` | v3 데이터셋 생성 리포트. 43건 처리, dev/test split, 통계 |
| `data/reports/pdf_analysis/claim_loop_full_review_pack_cohort4_v3_clean.md` | cohort4 생성 청구항, 원본 청구항, 평가지를 사람이 같이 볼 수 있게 묶은 리뷰팩 |
| `data/reports/pdf_analysis/claim_loop_v3_clean_quality_review.md` | v3 clean 정답지/생성본/평가지 품질 점검 |
| `data/reports/pdf_analysis/claim_extraction_bugfix_1020080137371.md` | 2008 케이스 청구항 추출 bugfix 관련 문서 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5_dataset_note.md` | skeleton test5 데이터셋과 당시 claim_count_control 가정 기록 |

### workflow별 결과 요약

| 파일/폴더 | 역할 |
|---|---|
| `data/reports/pdf_analysis/graph_claim_workflow_cohort4/` | graph workflow 4건 상세 결과 폴더 |
| `data/reports/pdf_analysis/graph_claim_workflow_cohort4/graph_claim_workflow_summary.md` | graph workflow 점수 요약 |
| `data/reports/pdf_analysis/graph_claim_workflow_cohort4/1020250193994/feedback_check_2025.md` | 사용자 피드백 기반 2025 케이스 과생성/도면참조번호/중복 점검 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/` | skeleton workflow 5건 상세 결과 폴더 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/claim_skeleton_workflow_summary.md` | skeleton workflow 점수 요약 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/summary.json` | complexity 기반 81점 케이스 요약 |

## JSON/JSONL 결과물

| 파일 | 역할 | 현재 점수/내용 |
|---|---|---|
| `data/reports/pdf_analysis/claim_loop_generated_cohort4_v3_clean.jsonl` | cohort4 GPT-5.5 생성 청구항 | 4건, 생성 청구항 15~20개 |
| `data/reports/pdf_analysis/claim_loop_evaluation_cohort4_v3_clean.jsonl` | cohort4 GPT-5.5 평가 결과 | 38, 68, 58, 62점 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/summary.json` | skeleton test5 최고 케이스 요약 | `1020157028995`, 81점, very_complex, 20항 생성 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/<patent_id>/00_public_no_reference.json` | 생성 입력. 원본 청구항 없음 | case별 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/<patent_id>/00_answer_key.json` | 원본/reference 청구항 | case별 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/<patent_id>/01_brief.json` | invention brief | case별 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/<patent_id>/02_graph.json` | invention graph | case별 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/<patent_id>/02b_claim_design.json` | claim design | case별 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/<patent_id>/03_claim_skeleton.json` | claim skeleton | case별 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/<patent_id>/04_generated_claims.json` | generated claims | case별 |
| `data/reports/pdf_analysis/claim_skeleton_workflow_test5/<patent_id>/05_evaluation.json` | 평가 결과 | case별 |

## prompt 조절 / human feedback이 들어간 지점

| 지점 | 파일 | 내용 |
|---|---|---|
| 과생성 피드백 | `graph_claim_workflow_cohort4/1020250193994/feedback_check_2025.md` | 원본 4항인데 23항 생성. `dependent_claim_candidates` 전부 펼친 문제 지적 |
| 도면 참조번호 피드백 | 같은 파일 | 원본 `(100)` 등 참조번호 42회, 생성본 0회. graph/schema/prompt가 보존 못한 문제 |
| 고정 claim count 문제 | `claim_skeleton_workflow_test5_dataset_note.md`, `session_handoff_claim_workflow_2026-05-14.md` | `4~8항, 복잡하면 최대 10항` 가정이 복잡 사건을 6항으로 압축 |
| complexity 기반 수정 | `claim_skeleton_workflow_test5/summary.json` | `1020157028995`: `very_complex`, target 20~28, 생성 20항, 81점 |
| human review 질문 | `claim_loop_evaluation_cohort4_v3_clean.jsonl`, 리뷰팩 | evaluator가 `human_review_questions`를 생성하고, 사람이 독립항 family/핵심 누락/권리범위 판단 |

## 주요 결과 숫자

### cohort4 v3 clean

| patent_id | year | 원본 청구항 | 생성 청구항 | 평가점수 | 판단 |
|---|---:|---:|---:|---:|---|
| 1020080137371 | 2008 | 5 | 15 | 38 | 실패. 원격 코드 업데이트 메시지 흐름을 놓침 |
| 1020157028995 | 2015 | 24 | 20 | 68 | 가장 낫지만 핵심 한정 일부 약함 |
| 1020200015713 | 2020 | 20 | 15 | 58 | 독립항 필수요건 약화 |
| 1020250193994 | 2025 | 4 | 15 | 62 | 도메인은 맞지만 과생성/세부 누락 |

### skeleton test5 최고점

```text
patent_id: 1020157028995
score: 81
complexity: very_complex
target: 20~28 claims
generated claims: 20
result folder: data/reports/pdf_analysis/claim_skeleton_workflow_test5/1020157028995/
```

## 현재 해석

1. 전날 loop의 핵심은 “청구항 문장 생성기”가 아니라 **claim skeleton / claim family / complexity 기반 설계 loop**다.
2. 사람 피드백은 별도 DB로 저장된 상태라기보다, Markdown 리뷰/평가지/handoff에 반영되어 다음 prompt 정책을 바꾼 상태다.
3. 아직 대량 확장하면 안 된다. GPT-5.5 호출은 최종 평가/선택 케이스 중심으로 제한해야 한다.
4. 다음 코드화 우선순위는 `case_card → delta_review → feedback_patch`처럼 사람 피드백을 작고 재사용 가능한 JSON/MD로 남기는 것이다.
