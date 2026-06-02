# Django 백엔드

기존 로그인/JWT 백엔드입니다. 사용자 계정, 로그인 화면, JWT API를 담당합니다.

## 실행

저장소 루트에서 실행합니다.

```bash
uv run python backend/django/manage.py migrate
uv run python backend/django/manage.py runserver 8000
```

## 접속

- 브라우저 UI: http://127.0.0.1:8000/accounts/login/
- 관리자 페이지: http://127.0.0.1:8000/admin/

관리자 계정은 로컬에서 직접 생성합니다.

```bash
uv run python backend/django/manage.py createsuperuser
```

## JWT REST API

### 회원가입

```text
POST /api/auth/signup/
```

요청 예시:

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

```text
POST /api/auth/login/
```

요청 예시:

```json
{
  "username": "user_id",
  "password": "password"
}
```

성공 응답에는 `access`, `refresh`, `user`가 포함됩니다.

### 내 정보 조회

```text
GET /api/auth/me/
Authorization: Bearer <access_token>
```

### 로그아웃

```text
POST /api/auth/logout/
Authorization: Bearer <access_token>
```

요청 예시:

```json
{
  "refresh": "refresh_token"
}
```

### 토큰 갱신

```text
POST /api/auth/token/refresh/
```

요청 예시:

```json
{
  "refresh": "refresh_token"
}
```

## DB 설정

기본값은 로컬 SQLite입니다.

```env
DJANGO_DB_ENGINE=django.db.backends.sqlite3
DJANGO_DB_NAME=backend/django/db.sqlite3
```

MySQL을 쓰려면 `.env`에 아래처럼 설정합니다.

```env
DJANGO_DB_ENGINE=django.db.backends.mysql
DJANGO_DB_NAME=patent_login
DJANGO_DB_USER=
DJANGO_DB_PASSWORD=
DJANGO_DB_HOST=localhost
DJANGO_DB_PORT=3306
```

실제 DB 비밀번호는 문서나 Git에 적지 않습니다.
