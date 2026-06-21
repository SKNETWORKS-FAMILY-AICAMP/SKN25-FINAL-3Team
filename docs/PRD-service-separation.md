# PRD: Django ↔ FastAPI 서비스 분리

**작성일**: 2026-06-21  
**상태**: Draft  
**관련 문서**: [PRD-logging-phoenix.md](PRD-logging-phoenix.md)

---

## 1. 배경 및 목적

현재 FastAPI AI 워커 서버는 기동 시 Django를 직접 부트스트랩한다.

```python
# backend/fastapi/main.py (현재)
sys.path.insert(0, os.path.join(os.getcwd(), 'backend', 'django'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
```

이 구조는 두 서비스가 코드 레벨에서 강하게 결합되어 있어 독립 배포, 독립 스케일링, 독립 테스트가 불가능하다.

### 목표

- FastAPI에서 Django 코드 의존성(`django.setup()`, Django ORM 등) 완전 제거
- 두 서비스가 **REST API**로만 통신하는 구조로 전환
- 서비스별 독립 배포 및 스케일링 가능하도록 경계 확립

---

## 2. 서비스 역할 정의

| 서비스 | 책임 | 포트 |
|--------|------|------|
| **Nginx** | 정적 파일(React `dist/`) 서빙, 요청 라우팅, 스트리밍 버퍼링 비활성화 | 80 |
| **Django** | 사용자 인증·세션, 프로젝트/워크스페이스 관리, 파일 업로드·다운로드, DB(ORM), FastAPI 스트리밍 응답 프록시 | 8000 |
| **FastAPI** | LangGraph AI 파이프라인 전담, LLM 호출, ndjson 스트리밍 응답 생성, Phoenix OTLP 트레이스 발생 | 8001 |

---

## 3. 아키텍처

### 통신 흐름

```
브라우저
  │ ① 페이지 요청
  ▼
Nginx :80
  ├─ /static/, /  → React dist/ 정적 파일 서빙
  └─ /workspace/, /api/, /auth/  → Django :8000 프록시
                                   (proxy_buffering off — 스트리밍 유지)
                                        │
                                        │ ② AI 요청
                                        │ POST /api/v1/generate-claims
                                        ▼
                                   FastAPI :8001
                                   LangGraph Pipeline
                                   (ndjson 스트리밍 응답 생성)
                                        │
                                        │ ③ 스트리밍 응답
                                        │ StreamingResponse (ndjson)
                                        ▼
                                   Django
                                   StreamingHttpResponse로 그대로 전달
                                        │
                                        │ ④ 브라우저로 스트리밍 전달
                                        ▼
                                   브라우저
                                   fetch() + ReadableStream으로 수신
```

> **스트리밍 핵심**: Nginx의 `proxy_buffering off` 설정이 없으면 Django까지 응답이 도달해도 Nginx가 전부 모았다가 한꺼번에 전달해 스트리밍이 깨진다.

### Docker Network 구성

```
┌──────────────────────────────────────────────────────────────┐
│                        Docker Network                         │
│                                                              │
│  Nginx :80                                                   │
│   ├─ React dist/ (정적)                                      │
│   ├─ → Django :8000  (proxy_buffering off)                   │
│   └─ → FastAPI :8001  (직접 호출 가능, 현재는 Django 경유)    │
│                                                              │
│  Django :8000    FastAPI :8001    Phoenix :6006              │
│                       │ OTLP ──────────→ │                   │
└──────────────────────────────────────────────────────────────┘
```

### 향후 고려: 브라우저 → FastAPI 직접 스트리밍

현재는 스트리밍이 `브라우저 → Django → FastAPI` 경로를 거친다. Django가 중간에서 프록시하므로 레이턴시가 추가된다. 트래픽이 늘거나 스트리밍 최적화가 필요해지면 아래 구조로 전환할 수 있다:

```
브라우저 → Django  (인증·CRUD만)
브라우저 → FastAPI (스트리밍 직접 수신)
```

이 경우 FastAPI에 CORS 설정과 JWT 검증 미들웨어가 추가로 필요하다.

---

## 4. 기능 요구사항

### FR-01: FastAPI Django 의존성 제거

- `backend/fastapi/main.py`에서 `sys.path.insert`, `django.setup()` 제거
- FastAPI 라우터에서 Django 모델·ORM 직접 import 제거
- FastAPI는 순수 Python 패키지(`agents/`, `pyproject.toml`)만 참조

### FR-02: Django → FastAPI 통신 명세 확정

- Django가 FastAPI를 호출하는 모든 엔드포인트 목록화
- 요청/응답 스키마를 Pydantic 모델로 명시 (FastAPI가 단일 진실 공급원)
- `FASTAPI_BASE_URL` 환경변수로 엔드포인트 주입

### FR-03: FastAPI 데이터 접근 방식 결정

FastAPI가 DB 데이터를 필요로 하는 경우 아래 중 하나를 선택:

| 방식 | 장점 | 단점 |
|------|------|------|
| Django REST API 경유 | 단일 DB 접근 주체 유지 | 레이턴시 추가 |
| FastAPI 전용 DB 연결 (SQLAlchemy 직접) | 빠름, 독립적 | DB 스키마 이중 관리 위험 |
| 요청 페이로드로 필요 데이터 전달 | 가장 단순 | 페이로드 증가 |

> 현재 코드 기준으로는 **요청 페이로드로 필요 데이터 전달** 방식이 가장 적합 (Django가 initial_state를 만들어 FastAPI에 넘기는 구조가 이미 존재).

### FR-04: docker-compose 서비스 독립성 확보

- `django_web`과 `fastapi_worker` 컨테이너가 서로의 소스를 마운트하지 않아도 동작
- 각 서비스 전용 `Dockerfile` 또는 `target` 스테이지 분리 검토

---

## 5. 구현 계획

### Phase 1: 현황 파악

- [ ] FastAPI 라우터 전체에서 Django import 목록 추출
- [ ] FastAPI가 실제로 DB를 직접 읽는 곳 식별
- [ ] Django → FastAPI 호출 엔드포인트 전체 목록화

### Phase 2: FastAPI 독립화

- [ ] `backend/fastapi/main.py` — `django.setup()` 블록 제거
- [ ] FastAPI 라우터에서 Django 모델 import 제거
- [ ] 필요한 데이터는 Django가 요청 페이로드에 포함하여 전달하도록 수정

### Phase 3: 통신 계약 정의

- [ ] Django → FastAPI 요청 스키마 Pydantic 모델로 확정
- [ ] FastAPI 응답 스키마 확정
- [ ] `FASTAPI_BASE_URL` 환경변수 `.env.example`에 추가

### Phase 4: 검증

- [ ] FastAPI 단독 기동 시 Django 없이 정상 동작 확인
- [ ] Django 단독 기동 시 오류 없음 확인
- [ ] E2E: 특허 생성 요청 → Django → FastAPI → 스트리밍 응답 정상 흐름 확인

---

## 6. 파일 변경 목록

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `backend/fastapi/main.py` | 수정 | `django.setup()` 블록 제거 |
| `backend/fastapi/routers/*.py` | 수정 | Django 모델 import 제거 |
| `backend/django/workspace/views.py` | 수정 | FastAPI 호출 시 필요 데이터 페이로드에 포함 |
| `.env.example` | 수정 | `FASTAPI_BASE_URL` 추가 |

---

## 7. 승인 기준 (Acceptance Criteria)

1. `fastapi_worker` 컨테이너 기동 시 Django 관련 import 오류 없음
2. `fastapi_worker` 단독으로 `/api/v1/generate-claims` 요청 처리 가능
3. E2E 특허 생성 흐름이 분리 전과 동일하게 동작
4. Phoenix 트레이스에 변화 없음 (계측 영향 없음)

---

## 8. 리스크

| 리스크 | 완화 방안 |
|--------|-----------|
| FastAPI 라우터 내 Django 의존성 누락 발견 | Phase 1에서 정적 분석(`grep -r "django"`)으로 전수 조사 |
| DB 스키마 공유 문제 | 요청 페이로드 전달 방식 우선 적용, DB 직접 연결은 필요 시만 도입 |
| 분리 후 인증 토큰 검증 위치 | JWT 검증은 Django에서 수행 후 FastAPI에 검증된 user_id만 전달 |
