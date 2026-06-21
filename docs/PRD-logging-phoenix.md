# PRD: 로깅 시스템 통합 및 Phoenix 모니터링 연동

**작성일**: 2026-06-21  
**상태**: Draft  

---

## 1. 배경 및 목적

현재 특허 AI 멀티에이전트 시스템(특허명세서 자동 작성 플랫폼)은 LangGraph 기반으로 SummaryAgent → ClaimAgent → ExaminerAgent → ClaimRewriteAgent 순의 파이프라인을 운영 중이다.

백엔드는 **Django**(웹·인증·DB)와 **FastAPI**(AI 워커·스트리밍) 두 독립 서비스로 분리 운영한다. Django는 사용자 요청을 받아 HTTP로 FastAPI를 호출하고, FastAPI는 LangGraph 파이프라인만 전담한다. 두 서비스는 코드 레벨 의존성 없이 REST API로만 통신한다.

### 현재 로깅 시스템의 문제

| 문제 | 내용 |
|------|------|
| `basicConfig()` 충돌 | 4개 에이전트 파일(`claim_agent.py`, `claim_rewrite_agent.py`, `drawing_agent.py`, `examiner.py`)에서 각자 `logging.basicConfig()` 호출 → Python 정책상 최초 호출만 유효, 나머지 무시 |
| 로깅 비활성 에이전트 | `examiner_agent.py`의 로깅 코드가 전면 주석 처리되어 심사관 에이전트 동작 추적 불가 |
| Correlation ID 없음 | 단일 특허 생성 요청이 여러 에이전트를 거치는 동안 요청 단위 추적 불가 |
| 토큰/비용 추적 없음 | GPT-4o, GPT-4o-mini 다수 호출 중이나 토큰 소비 및 API 비용 측정 수단 없음 |
| 에이전트 단계별 지연 측정 불가 | 어느 노드에서 병목이 발생하는지 알 수 없음 |
| 관찰 가능성(Observability) 도구 미연동 | `langsmith`가 의존성에 존재하나 `prior_art_agent.py`에만 부분 적용, 나머지 에이전트 미적용 |

### 목표

1. 전체 에이전트 파이프라인에 **일관된 중앙 로깅** 적용
2. **Arize Phoenix** 연동으로 LLM 트레이스, 토큰 사용량, 레이턴시를 시각적으로 모니터링
3. 운영/디버깅 효율성 향상 및 비용 가시성 확보

---

## 2. 범위

### In Scope

- Python 표준 `logging` 모듈 중앙 설정 모듈 신규 작성
- 각 에이전트 파일의 `basicConfig()` 호출 제거 및 정리
- Arize Phoenix 셀프 호스팅 설정 (Docker 컨테이너)
- FastAPI 서버에 OpenTelemetry + LangChain Instrumentation 적용
- docker-compose에 Phoenix 서비스 추가
- 환경변수 정리 (`.env` 항목 추가)
- **Django ↔ FastAPI 서비스 완전 분리** — FastAPI에서 Django 코드(`django.setup()`, Django ORM 등) 의존성 제거, REST API 통신으로 대체

### Out of Scope

- 외부 로그 수집 서비스 연동 (ELK, Datadog 등)
- LangSmith 전면 전환 (현행 prior_art_agent의 LangSmith 적용은 유지)
- Django 쪽 로깅 설정 변경 (Django LOGGING dict는 별도 태스크로 분리)
- 알림/Alert 시스템 구축
- Django ↔ FastAPI 서비스 분리 (→ [PRD-service-separation.md](PRD-service-separation.md) 참조)

---

## 3. 사용자 스토리

```
As a 개발자/멘티,
I want to LangGraph 파이프라인의 각 노드(에이전트)별 실행 시간, 입출력, LLM 토큰 수를
Phoenix UI에서 확인하고 싶다.
So that 병목 노드를 찾고 프롬프트 최적화 방향을 잡을 수 있다.
```

```
As a 운영자,
I want to 에러 발생 시 어느 에이전트에서 실패했는지 로그로 즉시 파악하고 싶다.
So that 원인 파악 시간을 줄일 수 있다.
```

```
As a 팀 리더,
I want to API 호출당 GPT 토큰 소비량과 모델별 비용 추이를 추적하고 싶다.
So that 월 API 비용을 예측하고 모델 선택을 최적화할 수 있다.
```

---

## 4. 기능 요구사항

### FR-01: 중앙 로깅 모듈

- **위치**: `agents/core/logging_config.py`
- `setup_logging(level: str)` 함수 하나로 전체 앱 로깅 설정
- 개발 환경: 읽기 쉬운 텍스트 포맷 (`%(asctime)s [%(levelname)s] %(name)s: %(message)s`)
- 프로덕션 환경(`ENV=prod`): JSON 포맷 (구조화 로그)
- 시끄러운 외부 라이브러리(`httpx`, `openai`, `langchain`) 레벨 WARNING으로 억제
- `logging.basicConfig()` 개별 호출은 전면 제거

### FR-02: Phoenix 서버 컨테이너화

- `docker-compose.yml`에 `phoenix` 서비스 추가
- Phoenix UI 포트: **6006**
- OTLP gRPC 포트: **4317** (에이전트 → Phoenix 트레이스 전송)
- 컨테이너 이미지: `arizephoenix/phoenix:latest`

### FR-03: OpenTelemetry + LangChain 자동 계측

- FastAPI `startup` 이벤트에서 `LangChainInstrumentor().instrument()` 호출
- 모든 LangChain/LangGraph 호출이 자동으로 Phoenix 트레이스에 기록됨
- 트레이스에 포함되는 정보:
  - 각 LangGraph 노드 이름 및 실행 시간
  - LLM 호출 입력 프롬프트 / 출력 텍스트 (선택적 마스킹)
  - 토큰 사용량 (prompt_tokens, completion_tokens, total_tokens)
  - 모델명 (gpt-4o, gpt-4o-mini 구분)
  - 예외 발생 시 스택 트레이스

### FR-04: Correlation ID (요청 추적)

- FastAPI 미들웨어에서 요청마다 UUID를 생성하여 `X-Request-ID` 헤더에 삽입
- 해당 ID가 로그와 Phoenix 트레이스 양쪽에 기록되어 연결 추적 가능

### FR-05: examiner_agent 로깅 복원

- `examiner_agent.py`의 주석 처리된 로깅 코드 복원
- 심사관 에이전트의 승인/반려 결과, 반복 횟수가 로그에 기록됨

---

## 5. 비기능 요구사항

| 항목 | 요구사항 |
|------|----------|
| 성능 | 트레이스 수집이 에이전트 응답 시간에 5ms 이상 영향 주지 않아야 함 (BatchSpanProcessor 사용) |
| 보안 | Phoenix UI는 내부 네트워크(Docker 내부)에서만 접근, 외부 노출 불가 |
| 이식성 | 환경변수 하나(`PHOENIX_COLLECTOR_ENDPOINT`)로 Phoenix 엔드포인트 변경 가능 |
| 로컬 실행 | Phoenix 없이도 에이전트가 정상 동작해야 함 (계측 실패 시 silent fail) |

---

## 6. 기술 스택 및 의존성

### 신규 추가 패키지

```toml
# pyproject.toml dependencies 추가
"arize-phoenix>=4.0.0",
"openinference-instrumentation-langchain>=0.1.0",
"opentelemetry-sdk>=1.24.0",
"opentelemetry-exporter-otlp>=1.24.0",
"python-json-logger>=2.0.7",  # JSON 포맷 로그 (프로덕션)
```

### 환경변수 추가 (`.env`)

```dotenv
# Phoenix 모니터링
PHOENIX_COLLECTOR_ENDPOINT=http://phoenix:6006/v1/traces   # Docker 환경
# PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces  # 로컬 개발

# 로깅 레벨
LOG_LEVEL=INFO
ENV=dev  # dev | prod
```

---

## 7. 모니터링 아키텍처

> 서비스 전체 아키텍처는 [PRD-service-separation.md](PRD-service-separation.md) 참조.  
> 여기서는 Phoenix 계측이 적용되는 범위만 표시한다.

```
FastAPI Worker :8001
  ├─ LangGraph Pipeline
  │   ├─ SummaryAgent   (gpt-4o-mini)
  │   ├─ ClaimAgent     (gpt-4o)
  │   ├─ ExaminerAgent  (gpt-4o)
  │   └─ RewriteAgent   (gpt-4o)
  │
  └─── OTLP ──→  Phoenix :6006 (UI)
                          :4317 (gRPC)
```

### Phoenix UI에서 확인 가능한 트레이스 구조

```
POST /api/v1/generate-claims  [X-Request-ID: abc-123]
└── LangGraph Pipeline
    ├── summary_node          [2.1s] [1,234 tokens] gpt-4o-mini
    ├── claim_node            [8.4s] [3,891 tokens] gpt-4o
    ├── examiner_node (1차)   [3.2s] [1,200 tokens] gpt-4o  → 반려
    ├── rewrite_node          [6.1s] [2,500 tokens] gpt-4o
    └── examiner_node (2차)   [3.0s] [1,180 tokens] gpt-4o  → 승인
```

---

## 8. 구현 계획

### Phase 1: 로깅 정리

- [ ] `agents/core/logging_config.py` 신규 작성
- [ ] `agents/claim_agent.py` — `basicConfig()` 제거
- [ ] `agents/claim_rewrite_agent.py` — `basicConfig()` 제거
- [ ] `agents/drawing_agent.py` — `basicConfig()` 제거
- [ ] `agents/examiner.py` — `basicConfig()` 제거
- [ ] `agents/examiner_agent.py` — 주석 처리된 로깅 복원
- [ ] FastAPI `startup`에서 `setup_logging()` 호출

### Phase 2: Phoenix 인프라

- [ ] `pyproject.toml` 의존성 4개 추가
- [ ] `docker-compose.yml`에 `phoenix` 서비스 추가
- [ ] `.env`에 `PHOENIX_COLLECTOR_ENDPOINT`, `LOG_LEVEL`, `ENV` 추가

### Phase 3: 계측 적용

- [ ] `backend/fastapi/main.py` — OTLP exporter + `LangChainInstrumentor` 설정
- [ ] FastAPI 미들웨어 — `X-Request-ID` Correlation ID 삽입
- [ ] 로컬에서 Phoenix UI 접속 확인 (http://localhost:6006)
- [ ] 테스트 요청 1건 전송 후 트레이스 가시성 검증

### Phase 4: 검증

- [ ] 각 에이전트 노드가 개별 스팬으로 기록되는지 확인
- [ ] 토큰 수 및 모델명 메타데이터 포함 여부 확인
- [ ] 에러 발생 시 스팬에 예외 정보 포함 확인
- [ ] Docker 환경에서 phoenix 컨테이너 연결 확인

---

## 9. 파일 변경 목록 요약

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `agents/core/logging_config.py` | 신규 | 중앙 로깅 설정 모듈 |
| `agents/claim_agent.py` | 수정 | `basicConfig()` 제거 |
| `agents/claim_rewrite_agent.py` | 수정 | `basicConfig()` 제거 |
| `agents/drawing_agent.py` | 수정 | `basicConfig()` 제거 |
| `agents/examiner.py` | 수정 | `basicConfig()` 제거 |
| `agents/examiner_agent.py` | 수정 | 로깅 주석 복원 |
| `backend/fastapi/main.py` | 수정 | Phoenix 계측, `setup_logging()` 호출, Correlation ID 미들웨어 |
| `docker-compose.yml` | 수정 | phoenix 서비스 추가 |
| `pyproject.toml` | 수정 | Phoenix 관련 의존성 4개 추가 |
| `.env` | 수정 | Phoenix/로깅 환경변수 추가 |

---

## 10. 승인 기준 (Acceptance Criteria)

1. `docker-compose up` 실행 후 http://localhost:6006 에서 Phoenix UI 접속 가능
2. `/api/v1/generate-claims` 호출 1건 시 Phoenix에 LangGraph 전체 파이프라인 트레이스 1건 기록
3. 각 에이전트 노드가 개별 스팬으로 분리되고 실행 시간이 표시됨
4. 각 LLM 호출 스팬에 `token_count.prompt`, `token_count.completion` 속성 포함
5. 에이전트 에러 발생 시 해당 스팬에 `error: true` 상태와 예외 메시지 포함
6. 로그 출력에서 `logging.basicConfig` 관련 경고 없음
7. Phoenix 컨테이너 중단 상태에서도 에이전트 파이프라인 정상 동작

---

## 11. 리스크 및 완화 방안

| 리스크 | 가능성 | 완화 방안 |
|--------|--------|-----------|
| Phoenix 컨테이너 리소스 과점 | 낮음 | 메모리 제한 설정 (`mem_limit: 512m`) |
| OTLP 연결 실패 시 에이전트 중단 | 중간 | `try/except`로 계측 초기화 감싸기, silent fail 보장 |
| 민감한 프롬프트 내용이 Phoenix에 저장 | 중간 | 배포 시 `PHOENIX_DISABLE_PAYLOAD_CAPTURE=true` 환경변수 활용 검토 |
| LangChain 버전 호환성 | 낮음 | `openinference-instrumentation-langchain` 버전 핀 고정 |
