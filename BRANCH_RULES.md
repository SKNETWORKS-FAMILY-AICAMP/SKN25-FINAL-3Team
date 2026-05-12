# GitHub 브랜치 이름 규칙

GitHub 협업이 처음인 팀원을 위한 **브랜치 이름 짓는 규칙**입니다.

## 핵심 원칙

```text
main = 최종 안정판
개인이름 = 개인 통합 브랜치
개인이름/type/작업내용 = 실제 작업 브랜치
```

예:

```text
main
hw
hw/docs/llm-wiki
gamja/feat/login
jisoo/fix/api-error
```

## 1. main

`main`은 최종 안정판입니다.

규칙:

- 직접 작업하지 않습니다.
- 최종 반영된 코드만 둡니다.
- 팀원이 공유/시연할 기준 브랜치입니다.

## 2. 개인 통합 브랜치

각자 자기 작업을 모아두는 브랜치입니다.

예:

```text
hw
gamja
jisoo
```

용도:

- 내 작업들을 모아서 확인하는 공간
- 아직 `main`에 넣기 애매한 작업 보관
- 여러 작업 브랜치를 합쳐서 테스트할 때 사용

## 3. 실제 작업 브랜치

기능 개발, 버그 수정, 문서 수정, 데이터 작업은 실제 작업 브랜치에서 합니다.

형식:

```text
<owner>/<type>/<short-description>
```

예:

```text
hw/docs/llm-wiki
hw/data/pilot-manifest
hw/feat/consultation-agent
hw/fix/pdf-download
hw/exp/prompt-comparison
```

## 4. type 규칙

| type | 의미 | 예시 |
|---|---|---|
| `feat` | 기능 개발 | `hw/feat/consultation-agent` |
| `fix` | 버그 수정 | `hw/fix/pdf-download` |
| `docs` | 문서 수정 | `hw/docs/llm-wiki` |
| `data` | 데이터/manifest 작업 | `hw/data/pilot-manifest` |
| `exp` | 실험/비교 | `hw/exp/prompt-comparison` |
| `refactor` | 구조 개선 | `hw/refactor/agent-state` |
| `test` | 테스트 | `hw/test/payload-validation` |
| `chore` | 설정/잡무 | `hw/chore/update-gitignore` |

## 5. 추천 사용 예시

현우가 LLM Wiki 문서를 고칠 때:

```bash
git checkout main
git pull origin main
git checkout hw
git merge main
git checkout -b hw/docs/llm-wiki
```

현우가 상담 에이전트 기능을 만들 때:

```bash
git checkout main
git pull origin main
git checkout hw
git merge main
git checkout -b hw/feat/consultation-agent
```

## 6. 피할 이름

아래처럼 의미가 애매한 이름은 피합니다.

```text
test
final
new
backup
mybranch
hw-main
```

이유:

- 무슨 작업인지 모릅니다.
- 누가 관리하는지 헷갈립니다.
- 나중에 지워도 되는 브랜치인지 판단하기 어렵습니다.

## 최종 요약

```text
main = 안정판
hw = 현우 개인 통합 브랜치
hw/docs/... = 현우 문서 작업
hw/data/... = 현우 데이터 작업
hw/feat/... = 현우 기능 작업
hw/fix/... = 현우 버그 수정
hw/exp/... = 현우 실험 작업
```
