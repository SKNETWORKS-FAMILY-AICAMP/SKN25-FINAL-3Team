# ADR-005: Django · FastAPI · Frontend 독립 배포 단위 분리

**상태:** Accepted  
**날짜:** 2026-06-13  
**대체:** ADR-001의 배포 구조 섹션을 확장

## 맥락

ADR-001은 Django(인증)와 FastAPI(파이프라인)를 코드 수준에서 분리하는 결정이었다.  
이 시점까지는 두 서비스를 하나의 Docker Compose 스택에서 함께 올렸고, 프론트엔드는 Vite 개발 서버가 내부에서 프록시 역할을 맡았다.

```
[Vite :3000]  ← /api/*  → fastapi:8080
              ← /auth/* → django:8000
```

이 구성은 로컬 개발에는 충분하지만, 운영 배포에서 아래 문제가 생긴다.

- **스케일링 단위가 묶임**: Agent 파이프라인이 부하를 받을 때 Django 인증 서버도 함께 스케일해야 한다.
- **배포 주기가 다름**: 프론트엔드 UI 변경, 인증 로직 변경, Agent 로직 변경은 각각 독립적으로 배포하고 싶다.
- **Vite 프록시는 프로덕션 용도가 아님**: 정적 빌드 결과물(`npm run build`)을 서빙할 때 프록시 설정이 사라진다.

## 결정

Django, FastAPI(Agent API), React Frontend를 **세 개의 독립 배포 단위**로 분리한다.

```
[Browser]
  ↓ 정적 자산 요청
[Frontend — S3 + CloudFront 또는 별도 서버]
  ↓ /api/auth/* 직접 호출
[Django — 인증 전용 서버 (EC2 또는 컨테이너)]
  ↓ /api/* 직접 호출
[FastAPI — Agent API 서버 (EC2 또는 컨테이너)]
  ↓
[PostgreSQL]  [Redis]  [AWS vLLM (Critic Agent)]
```

각 서비스의 책임 범위:

| 서비스 | 역할 | 외부 노출 포트 |
|--------|------|--------------|
| **Frontend** | React SPA 정적 빌드 서빙 | 80 / 443 |
| **Django** | JWT 인증 API (`/api/auth/*`) | 8000 |
| **FastAPI** | Agent 파이프라인 API (`/api/*`) | 8080 |

## 이유

- **독립 스케일링**: Agent API는 LLM 호출로 오래 걸린다. Django 인증 서버를 함께 스케일할 이유가 없다.
- **배포 주기 분리**: 프론트엔드 핫픽스가 Agent API 배포를 기다릴 필요가 없다.
- **프론트엔드 정적 서빙**: React 빌드 결과물은 S3/CloudFront에서 서빙하면 서버 부하와 무관하게 빠르게 전달된다. Vite dev proxy에 의존할 필요가 없다.
- **CORS 명시화**: 프록시로 숨겨져 있던 출처(origin) 경계가 명확해지고, 각 서비스가 허용할 origin을 직접 선언한다.

## 결과

### 프론트엔드 변경

Vite 프록시(`/api/*`, `/auth/*`)는 **개발 환경 전용**으로만 유지한다.  
프로덕션 빌드에서는 환경변수로 각 서비스 엔드포인트를 직접 지정한다.

```dotenv
# frontend/.env.production
VITE_API_BASE_URL=https://api.patent-service.example.com
VITE_AUTH_BASE_URL=https://auth.patent-service.example.com
```

### Django CORS 설정

FastAPI와 Frontend의 origin을 Django `CORS_ALLOWED_ORIGINS`에 추가해야 한다.

```python
# backend/django/config/settings.py
CORS_ALLOWED_ORIGINS = [
    "https://patent-service.example.com",   # Frontend
    "https://api.patent-service.example.com",  # FastAPI (서버 간 호출)
]
```

### FastAPI CORS 설정

Frontend origin을 허용한다 (`.env`의 `CORS_ORIGINS`).

```dotenv
CORS_ORIGINS=https://patent-service.example.com
```

### Docker Compose 역할

`docker-compose.yml`은 **로컬 개발 및 통합 테스트 전용**으로 위상이 바뀐다.  
프로덕션 배포는 각 서비스 별도 Dockerfile(`docker/Dockerfile.django`, `docker/Dockerfile.fastapi`, `docker/Dockerfile.frontend`)을 사용한다.

### JWT 토큰 검증

FastAPI가 Django의 JWT를 직접 검증해야 하는 경우, 동일한 `SECRET_KEY`를 공유하거나 Django의 `/api/auth/me/` 엔드포인트를 내부 호출해 토큰을 검증한다.
