---
title: Team Collaboration Guide
created: 2026-05-12
updated: 2026-05-15
type: guide
tags: [collaboration, data]
sources: []
confidence: high
---

# Team Collaboration Guide

## 한 줄 요약

처음 협업하는 팀원이 실수하지 않도록, Git에 넣을 것과 넣지 않을 것을 명확히 나눕니다.

## Git 브랜치 규칙

브랜치 생성, 최신 main 반영, push, PR 생성의 기본 규칙은 repo 루트의 [`BRANCH_RULES.md`](../../../BRANCH_RULES.md)를 따릅니다.

이 문서는 거기에 더해서 **PDF/데이터 파일을 Git에 잘못 올리지 않기 위한 프로젝트 전용 규칙**을 정리합니다.

## 제일 중요한 규칙 6개

1. `main`에서 직접 작업하지 않습니다.
2. 작업 전 `git pull origin main` 또는 내 브랜치에 최신 main을 merge합니다.
3. PDF, SQLite, 대량 리포트는 Git에 넣지 않습니다.
4. 데이터 위치는 manifest에 기록합니다.
5. 새 결정은 LLM Wiki에 짧게 남깁니다.
6. `main` 반영 PR에는 담당자별 확인 체크리스트와 PM 확인 체크리스트를 둡니다.

## 개발할 때 LLM Wiki 쓰는 순서

개발 전/중/후에 문서를 어떻게 봐야 하는지는 [[developer-workflow-scenario]]를 따릅니다.

짧게 말하면:

1. 개발 전: 관련 Wiki 문서 확인
2. 개발 중: 코드가 Wiki와 달라지면 TODO 또는 수정
3. 개발 후: 코드 변경에 맞춰 Wiki도 같이 수정
4. push 전: `git status --short`로 대용량/민감 파일 확인

## 작업 시작 순서

```bash
git checkout main
git pull origin main
git checkout 내브랜치명
git merge main
```

또는 내 브랜치에서 바로:

```bash
git fetch origin
git merge origin/main
```

## 데이터 파일 규칙

| 파일 종류 | 예시 | Git에 올림? |
|---|---|---|
| Wiki 문서 | `docs/llm-wiki/*.md` | 예 |
| 스키마/작은 예시 | `docs/llm-wiki/schemas/*.md`, `data/processed/examples/*.json` | 예 |
| Drive inventory | `data/manifests/*.jsonl` | 예 |
| 청구항 학습 JSONL | `data/processed/claim_loop/training/*.jsonl` | 작은 학습셋만 예 |
| 청구항 실험 노트북 | `notebooks/claim/*.ipynb` | 예 |
| 모델 설정 | `models/claim/configs/*` | 예 |
| 모델 가중치/checkpoint | `models/**/*.safetensors`, `models/**/checkpoint-*` | 아니오 |
| PDF | `data/raw/pdfs/*.pdf` | 아니오 |
| 추출 TXT 대량 | `data/raw/texts/*.txt` | 아니오 |
| SQLite | `*.sqlite3` | 아니오 |
| HTML 실험 리포트 | `data/reports/*.html` | 아니오 |
| `.env` | API key 포함 | 절대 아니오 |

## commit 전 확인

```bash
git status --short
git diff --stat
```

PDF나 SQLite가 보이면 보통 잘못된 상태입니다.

## PR 확인 체크리스트

`main` 반영 PR에는 repo 루트의 `BRANCH_RULES.md`에 있는 체크리스트를 사용합니다.

구성:

1. 공통 체크리스트
2. 은석 확인 체크리스트
3. 가영 확인 체크리스트
4. 범수 확인 체크리스트
5. 서현 확인 체크리스트
6. 홍익 확인 체크리스트
7. PM 확인 체크리스트

담당자는 자기 이름의 체크리스트만 확인하고, PM은 마지막에 PM 확인 체크리스트를 확인합니다.

## LLM Wiki 수정 규칙

문서를 새로 만들면:

1. frontmatter를 붙입니다.
2. 관련 문서 2개 이상을 Obsidian식 wiki link로 연결합니다.
3. `index.md`에 한 줄 요약을 추가합니다.
4. `log.md`에 작업 내용을 기록합니다.

## 관련 문서

- [[data-management-strategy]]
- [[pipeline-and-evaluation]]
- [[pilot-600-v1]]
