# GitHub 협업 기본 규칙

GitHub 협업이 처음인 팀원을 위한 아주 간단한 규칙입니다.

## 핵심 규칙

- `main` 브랜치에서 직접 작업하지 않기
- 작업할 때는 각자 자기 브랜치를 만들어서 작업하기
- 작업 시작 전에는 항상 최신 코드 받기
- 작업 끝나면 GitHub에 올리고 Pull Request 만들기
- 충돌 나면 혼자 막 고치지 말고 팀원에게 공유하기

---

## 1. 처음 프로젝트 받기

처음 한 번만 실행합니다.

```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN25-FINAL-3Team.git
cd SKN25-FINAL-3Team
```

---

## 2. 작업 시작 전에 최신 코드 받기

작업 시작 전에는 항상 `main`을 최신 상태로 맞춥니다.

```bash
git checkout main
git pull origin main
```

---

## 3. 내 작업 브랜치 만들기

```bash
git checkout -b feature/이름-작업내용
```

예시:

```bash
git checkout -b feature/hyunwoo-login
git checkout -b feature/minji-main-page
git checkout -b fix/jisoo-api-error
```

브랜치 이름은 간단하게:

```text
feature/이름-작업내용
fix/이름-수정내용
```

---

## 4. 작업한 내용 저장하기

작업 후 아래 순서대로 실행합니다.

```bash
git add .
git commit -m "작업 내용 간단히 작성"
```

예시:

```bash
git commit -m "로그인 화면 추가"
git commit -m "메인 페이지 수정"
git commit -m "API 오류 수정"
```

---

## 5. 내 브랜치를 GitHub에 올리기

처음 올릴 때:

```bash
git push -u origin 브랜치명
```

예시:

```bash
git push -u origin feature/hyunwoo-login
```

그 다음부터는 간단히:

```bash
git push
```

---

## 6. 작업 끝나면 Pull Request 만들기

GitHub 사이트에서 진행합니다.

1. GitHub 저장소 접속
2. `Compare & pull request` 클릭
3. 내용 간단히 적기
4. Pull Request 생성
5. 팀원 확인 후 `main`에 합치기

---

## 7. main 최신 내용 내 브랜치에 합치기

다른 팀원이 작업한 내용이 `main`에 합쳐졌다면, 내 브랜치에도 가져옵니다.

```bash
git checkout main
git pull origin main
git checkout 내브랜치명
git merge main
```

예시:

```bash
git checkout main
git pull origin main
git checkout feature/hyunwoo-login
git merge main
```

충돌이 안 나면 그대로 작업을 계속하면 됩니다.

충돌이 나면 팀원에게 공유하고 같이 해결합니다.

---

## 8. 자주 쓰는 명령어 요약

현재 브랜치 확인:

```bash
git branch
```

변경된 파일 확인:

```bash
git status
```

최신 코드 받기:

```bash
git pull origin main
```

작업 저장:

```bash
git add .
git commit -m "작업 내용"
```

GitHub에 올리기:

```bash
git push
```

---

## 제일 많이 쓰는 흐름

작업 시작:

```bash
git checkout main
git pull origin main
git checkout -b feature/이름-작업내용
```

작업 완료:

```bash
git add .
git commit -m "작업 내용"
git push -u origin feature/이름-작업내용
```

그 다음 GitHub에서 Pull Request를 만들면 됩니다.
