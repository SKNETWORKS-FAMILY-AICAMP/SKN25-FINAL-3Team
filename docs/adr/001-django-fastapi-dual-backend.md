# ADR-001: Django + FastAPI 이중 백엔드

**상태:** Accepted  
**날짜:** 2026-06-02  
**참고:** 배포 단위 분리(독립 서버 배포)는 → [ADR-005](005-separate-deployment-units.md)

## 맥락

백엔드 서버를 단일 프레임워크로 구성하는 방법과 두 프레임워크로 분리하는 방법 중 선택이 필요했다.

후보:
1. Django 단일 백엔드 (DRF로 파이프라인 API 추가)
2. FastAPI 단일 백엔드 (JWT 인증 직접 구현)
3. Django(인증) + FastAPI(파이프라인) 분리

## 결정

Django는 JWT 인증(회원가입·로그인·토큰 갱신·블랙리스트)만 담당하고,  
FastAPI는 멀티에이전트 파이프라인과 비즈니스 로직 전체를 담당한다.

```
POST /api/auth/*   → django:8000   (JWT, djangorestframework-simplejwt)
GET|POST /api/*    → fastapi:8080  (파이프라인, agent 실행, 결과 조회)
```

## 이유

- **인증**: `djangorestframework-simplejwt`는 토큰 블랙리스트, refresh 회전, 사용자 모델 확장을 코드 없이 제공한다. FastAPI에서 같은 수준을 구현하려면 상당한 추가 코드가 필요하다.
- **파이프라인**: FastAPI의 `async`/`await`와 `asyncio.to_thread()`는 LLM 호출처럼 오래 걸리는 동기 작업을 이벤트 루프를 막지 않고 처리하는 데 유리하다. Django의 WSGI 기반 동기 뷰는 이 패턴과 맞지 않는다.
- **역할 분리**: 인증과 파이프라인을 분리하면 각 서비스를 독립적으로 스케일하거나 교체할 수 있다.

## 결과

- 컨테이너가 두 개(django, fastapi)로 늘어난다.
- 프론트엔드는 `/auth/*`와 `/api/*` 두 경로로 요청을 나눠야 한다 (Vite 프록시 설정).
- DB는 하나를 공유하지만 Django ORM과 SQLAlchemy가 각자 다른 테이블을 관리한다 (→ ADR-002).
