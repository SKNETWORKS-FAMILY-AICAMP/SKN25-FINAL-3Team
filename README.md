# SKN25-FINAL-3Team

# 🚨 Git 사용 규칙: `main`에 직접 push 금지

팀 작업은 각자 브랜치에서 진행하고, `main`에 반영할 때는 반드시 **PR(Pull Request)** 을 올립니다.

```text
작업 브랜치에서 개발
→ GitHub에 push
→ main으로 PR 생성
→ 최종 PM 확인
→ merge
```

## 절대 금지

- `main` 브랜치에 직접 push하지 않습니다.
- 대용량 PDF/TXT/SQLite/HTML 리포트, 임시 파일, `.env` 같은 비밀값을 올리지 않습니다.
- 검증하지 않은 코드를 바로 `main`에 합치지 않습니다.

## PR 올릴 때 확인

- [ ] 작업 목적을 PR 설명에 적었습니다.
- [ ] 변경 파일에 불필요한 대용량 파일/임시 파일/비밀값이 없습니다.
- [ ] 실행 또는 검증 방법을 적었습니다.
- [ ] 문서 변경이 필요한 경우 관련 문서를 수정했습니다.
- [ ] 최종 PM 확인을 받습니다.

자세한 브랜치/PR 규칙은 [BRANCH_RULES.md](BRANCH_RULES.md)를 먼저 읽어주세요.

---

AI/소프트웨어 특허 상담 및 선행기술 분석 프로젝트입니다.

## 먼저 읽을 문서

프로젝트 데이터 관리, 스키마, 파이프라인, 평가 기준은 LLM Wiki에서 관리합니다.

- [Git 브랜치 규칙](BRANCH_RULES.md)
- [LLM Wiki 시작 문서](docs/llm-wiki/README.md)
- [LLM Wiki 목차](docs/llm-wiki/index.md)
- [팀 협업 가이드](docs/llm-wiki/concepts/team-collaboration-guide.md)
- [데이터 관리 전략](docs/llm-wiki/concepts/data-management-strategy.md)
- [Pilot 600 데이터셋](docs/llm-wiki/concepts/pilot-600-v1.md)
- [특허 데이터 스키마](docs/llm-wiki/concepts/patent-data-schemas.md)
- [파이프라인과 평가](docs/llm-wiki/concepts/pipeline-and-evaluation.md)

## 데이터 폴더

- [data 폴더 설명](data/README.md)
- 대량 PDF/TXT/SQLite/HTML 리포트는 Git에 올리지 않습니다.
- Google Drive/GCS 원천 위치는 `data/manifests/`에서 관리합니다.
