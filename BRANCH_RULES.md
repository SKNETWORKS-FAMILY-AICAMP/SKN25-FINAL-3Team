# GitHub 브랜치 이름과 PR 확인 규칙

GitHub 협업이 처음인 팀원을 위한 **브랜치 이름 + PR 확인 체크리스트**입니다.

## 핵심 원칙

```text
main = 최종 안정판
개인이름 = 개인 통합 브랜치
개인이름/type/작업내용 = 실제 작업 브랜치
```

예:

```text
main
name
name/docs/llm-wiki
name/feat/login
name/fix/api-error
```

여기서 `name`은 각자 정한 짧은 이름을 씁니다.

예:

```text
본인 이름, 영문 이니셜, GitHub ID 일부 등
```

## 1. main

`main`은 최종 안정판입니다.

규칙:

- 직접 작업하지 않습니다.
- 최종 반영된 코드만 둡니다.
- 팀원이 공유/시연할 기준 브랜치입니다.

## 2. 개인 통합 브랜치

각자 자기 작업을 모아두는 브랜치입니다.

형식:

```text
<name>
```

예:

```text
name
user
member
```

용도:

- 내 작업들을 모아서 확인하는 공간
- 아직 `main`에 넣기 애매한 작업 보관
- 여러 작업 브랜치를 합쳐서 테스트할 때 사용

## 3. 실제 작업 브랜치

기능 개발, 버그 수정, 문서 수정, 데이터 작업은 실제 작업 브랜치에서 합니다.

형식:

```text
<name>/<type>/<short-description>
```

예:

```text
name/docs/llm-wiki
name/data/pilot-manifest
name/feat/consultation-agent
name/fix/pdf-download
name/exp/prompt-comparison
```

## 4. type 규칙

| type | 의미 | 예시 |
|---|---|---|
| `feat` | 기능 개발 | `name/feat/consultation-agent` |
| `fix` | 버그 수정 | `name/fix/pdf-download` |
| `docs` | 문서 수정 | `name/docs/llm-wiki` |
| `data` | 데이터/manifest 작업 | `name/data/pilot-manifest` |
| `exp` | 실험/비교 | `name/exp/prompt-comparison` |
| `refactor` | 구조 개선 | `name/refactor/agent-state` |
| `test` | 테스트 | `name/test/payload-validation` |
| `chore` | 설정/잡무 | `name/chore/update-gitignore` |

## 5. 추천 사용 예시

LLM Wiki 문서를 고칠 때:

```bash
git checkout main
git pull origin main
git checkout <name>
git merge main
git checkout -b <name>/docs/llm-wiki
```

상담 에이전트 기능을 만들 때:

```bash
git checkout main
git pull origin main
git checkout <name>
git merge main
git checkout -b <name>/feat/consultation-agent
```

데이터 manifest 작업을 할 때:

```bash
git checkout main
git pull origin main
git checkout <name>
git merge main
git checkout -b <name>/data/pilot-manifest
```

## 6. PR 규칙: `main`에 넣을 때만 사용

GitHub에서는 **PR(Pull Request)** 라고 부릅니다.
GitLab에서는 비슷한 기능을 **MR(Merge Request)** 라고 부릅니다.
우리 문서에서는 GitHub 기준으로 **PR**이라고 씁니다.

규칙:

- 개인 브랜치끼리 작업을 옮기거나 테스트할 때는 PR이 필수는 아닙니다.
- **`main`에 반영할 때만 PR을 사용합니다.**
- `main`에 직접 push하지 않습니다.
- PR은 최종 반영 전에 팀원이 각자 자기 작업을 확인하고, PM이 마지막으로 확인하는 기록용 절차입니다.

## 7. PR 본문 체크리스트

PR을 만들 때 아래 체크리스트를 본문에 넣습니다.

### 공통 체크리스트

```markdown
## 공통 체크리스트

- [ ] 작업 목적이 PR 설명에 적혀 있다.
- [ ] 변경 파일에 불필요한 대용량 파일, 임시 파일, 비밀값이 없다.
- [ ] 실행/검증 방법을 적었다.
- [ ] 문서 변경이 필요한 경우 관련 문서를 업데이트했다.
- [ ] 충돌 없이 `main` 기준 최신 상태에서 확인했다.
```

### 은석 확인 체크리스트

```markdown
## 은석 확인 체크리스트

- [ ] 은석 담당 변경사항을 직접 확인했다.
```

### 가영 확인 체크리스트

```markdown
## 가영 확인 체크리스트

- [ ] 가영 담당 변경사항을 직접 확인했다.
```

### 범수 확인 체크리스트

```markdown
## 범수 확인 체크리스트

- [ ] 범수 담당 변경사항을 직접 확인했다.
```

### 서현 확인 체크리스트

```markdown
## 서현 확인 체크리스트

- [ ] 서현 담당 변경사항을 직접 확인했다.
```

### 홍익 확인 체크리스트

```markdown
## 홍익 확인 체크리스트

- [ ] 홍익 담당 변경사항을 직접 확인했다.
```

### PM 확인 체크리스트

PM은 팀원별 확인이 끝난 뒤 최종 반영 여부만 확인합니다.

```markdown
## PM 확인 체크리스트

- [ ] 작업 목적이 PR 설명에 적혀 있다.
- [ ] 변경 파일에 불필요한 대용량 파일, 임시 파일, 비밀값이 없다.
- [ ] 실행/검증 방법을 적었다.
- [ ] 문서 변경이 필요한 경우 관련 문서를 업데이트했다.
- [ ] 충돌 없이 `main` 기준 최신 상태에서 확인했다.
- [ ] 최종 PM 확인을 받았다.
```

## 8. 피할 이름

아래처럼 의미가 애매한 이름은 피합니다.

```text
test
final
new
backup
mybranch
main2
```

이유:

- 무슨 작업인지 모릅니다.
- 누가 관리하는지 헷갈립니다.
- 나중에 지워도 되는 브랜치인지 판단하기 어렵습니다.

## 최종 요약

```text
main = 안정판, 직접 push 금지
main 반영 = PR 사용 + 팀원별 확인 체크리스트 + 최종 PM 확인
<name> = 개인 통합 브랜치
<name>/docs/... = 문서 작업
<name>/data/... = 데이터 작업
<name>/feat/... = 기능 작업
<name>/fix/... = 버그 수정
<name>/exp/... = 실험 작업
```
