# Django 백엔드 — PYPI 웹 서버

PYPI(화이트톤 로펌 스타일) 랜딩 페이지 + 로그인/회원가입/대시보드 + 워크스페이스(특허 작성 파이프라인)가 통합된 Django 웹 서버입니다.

---

## 빠른 시작

### 1. 브랜치 체크아웃

```bash
git checkout bizseohyunkim
```

### 2. `backend/django` 폴더로 이동

```bash
cd backend/django
```

### 3. 의존성 설치

Python 3.10+ 환경에서 실행합니다.

```bash
pip install -r ../../requirements.txt
```

> `uv`를 쓰는 경우 저장소 루트에서 `uv sync` 한 번 실행하면 됩니다.

### 4. DB 마이그레이션

```bash
python manage.py migrate
```

### 5. 서버 실행

```bash
python manage.py runserver 8000
```

### 6. 브라우저 접속

| 페이지 | URL |
|---|---|
| 랜딩 페이지 (PYPI 화이트톤) | http://localhost:8000/ |
| 로그인 | http://localhost:8000/accounts/login/ |
| 회원가입 | http://localhost:8000/accounts/signup/ |
| 대시보드 | http://localhost:8000/accounts/dashboard/ |
| 워크스페이스 | http://localhost:8000/workspace/ |
| 관리자 페이지 | http://localhost:8000/admin/ |

---

## 관리자 계정 생성 (선택)

```bash
python manage.py createsuperuser
```

---

## DB 설정

기본값은 SQLite(로컬 개발용)입니다. 별도 설정 없이 바로 실행됩니다.

```env
DJANGO_DB_ENGINE=django.db.backends.sqlite3
DJANGO_DB_NAME=db.sqlite3
```

MySQL로 전환하려면 프로젝트 루트에 `.env` 파일을 만들고 아래처럼 설정합니다.

```env
DJANGO_DB_ENGINE=django.db.backends.mysql
DJANGO_DB_NAME=patent_login
DJANGO_DB_USER=your_user
DJANGO_DB_PASSWORD=your_password
DJANGO_DB_HOST=localhost
DJANGO_DB_PORT=3306
```

> 실제 비밀번호는 절대 Git에 올리지 않습니다.

---

## JWT REST API

로그인 후 발급된 `access` 토큰을 `Authorization: Bearer <token>` 헤더에 담아 사용합니다.

### 회원가입

```
POST /api/auth/signup/
```

```json
{
  "username": "user_id",
  "name": "사용자 이름",
  "gender": "M",
  "age": 25,
  "password": "password",
  "password2": "password"
}
```

### 로그인 / 토큰 발급

```
POST /api/auth/login/
```

```json
{
  "username": "user_id",
  "password": "password"
}
```

응답: `access`, `refresh`, `user`

### 내 정보 조회

```
GET /api/auth/me/
Authorization: Bearer <access_token>
```

### 로그아웃

```
POST /api/auth/logout/
Authorization: Bearer <access_token>
```

```json
{ "refresh": "refresh_token" }
```

### 토큰 갱신

```
POST /api/auth/token/refresh/
```

```json
{ "refresh": "refresh_token" }
```
