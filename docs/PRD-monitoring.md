# PRD: 서비스 모니터링 — 수집 지표 및 관찰 방법

**작성일**: 2026-06-21  
**상태**: Draft  
**관련 문서**: [PRD-logging-phoenix.md](PRD-logging-phoenix.md) · [PRD-service-separation.md](PRD-service-separation.md)

---

## 1. 배경 및 목적

[PRD-logging-phoenix.md](PRD-logging-phoenix.md)에서 LLM 트레이스(Arize Phoenix)와 중앙 로깅이 정의되었다.  
이 문서는 그 위에 **서비스 전체의 건강 상태**를 숫자로 측정하고 눈으로 볼 수 있게 하는 모니터링 계층을 정의한다.

### 모니터링이 없으면 생기는 문제

| 상황 | 현재 상태 |
|------|----------|
| API 응답이 느려졌다 | 언제부터인지, 어느 서비스인지 모름 |
| 특허 생성 요청이 자꾸 실패한다 | 에러율 추이를 볼 수단 없음 |
| OpenAI API 비용이 예상보다 많이 나온다 | 모델별/엔드포인트별 집계 없음 |
| 컨테이너 중 하나가 죽어 있다 | 헬스체크 엔드포인트 없음 |

### 목표

1. **RED 지표** — 요청 수(Rate), 에러율(Error), 응답 시간(Duration) 기준으로 각 서비스 건강 상태를 숫자로 확인
2. **LLM 비용 지표** — 에이전트별 토큰 소비·API 비용을 집계해 월 예산을 예측
3. **헬스체크** — 각 서비스의 살아있음을 단일 엔드포인트로 확인
4. **대시보드** — 위 지표를 한 화면에서 볼 수 있는 뷰 제공

---

## 2. 모니터링 대상 서비스

### 배포 환경

서비스는 **AWS EC2 단일 인스턴스** 위에서 Docker Compose로 운영된다.

```
[ 인터넷 ]
     │
     ▼
  EC2 인스턴스 (Ubuntu)
  ┌──────────────────────────────────────────┐
  │  Docker Compose 네트워크                  │
  │                                          │
  │  Frontend     :3000                      │
  │  Django       :8000  (웹·인증·DB)         │
  │  FastAPI      :8001  (LangGraph AI)      │
  │  Phoenix      :6006  (LLM 트레이스 UI)   │
  │                  │ OTLP :4317            │
  └──────────────────────────────────────────┘
     │
     ▼
  AWS CloudWatch  (EC2 시스템 지표 + 로그)
```

모니터링은 3개 계층으로 분리된다:

| 계층 | 대상 | 도구 |
|------|------|------|
| **LLM 트레이스** | 에이전트 스팬·토큰 | Phoenix (이미 구현) |
| **서비스 HTTP 지표** | Django·FastAPI 요청/에러/레이턴시 | 헬스체크 + 구조화 로그 |
| **EC2 인프라 지표** | CPU·메모리·디스크·네트워크 | AWS CloudWatch |

이 PRD는 Django·FastAPI 두 Python 서비스의 **서비스 수준 지표**와 **EC2 인프라 지표**를 다룬다.  
LLM 트레이스(스팬·토큰 상세)는 Phoenix가 담당하며 중복 정의하지 않는다.

---

## 3. 수집해야 할 지표 목록

### 3-1. HTTP API 지표 (RED 메서드)

> 두 서비스(Django, FastAPI) 모두에 적용

| 지표 | 측정 방법 | 왜 필요한가 |
|------|-----------|------------|
| **요청 수 (RPS)** | 초당 처리 요청 수, 엔드포인트별 분류 | 트래픽 패턴 파악, 피크 타임 식별 |
| **에러율** | 5xx 응답 비율 (목표 < 1%) | 장애 조기 탐지 |
| **응답 시간 P50/P95/P99** | 중앙값·95번째·99번째 백분위 레이턴시 | "평균"은 이상치를 숨김 — 백분위로 실제 체감 속도 파악 |

**FastAPI 핵심 엔드포인트 별도 추적**

| 엔드포인트 | 중점 지표 |
|-----------|----------|
| `POST /api/v1/generate-claims` | P95 응답 시간, 에러율 (파이프라인 전체 소요) |
| `POST /api/v1/generate-drawings` | P95 응답 시간 |
| `POST /api/v1/generate-specification` | P95 응답 시간 |

**경보 임계값 (초기 권장)**

```
P95 응답 시간 > 30초  → WARNING  (특허 생성은 기본 10~20초 예상)
P95 응답 시간 > 60초  → CRITICAL
에러율 > 5%           → WARNING
에러율 > 10%          → CRITICAL
```

---

### 3-2. LLM 비용·품질 지표

> Phoenix가 스팬 단위 데이터를 저장하므로, 집계는 Phoenix UI 또는 Phoenix API로 조회

| 지표 | 단위 | 집계 방법 |
|------|------|----------|
| **총 토큰 소비량** | tokens/요청, tokens/일 | Phoenix "Token Count" 컬럼 집계 |
| **모델별 토큰 분포** | gpt-4o vs gpt-4o-mini 비율 | Phoenix 필터 `model_name` 기준 그룹 |
| **추정 비용** | 원/일, 원/월 | 토큰 수 × 모델 단가 (별도 계산 시트) |
| **에이전트별 레이턴시** | ms, 스팬 단위 | Phoenix 트레이스 뷰 → 각 노드 duration |
| **ExaminerAgent 재시도 횟수** | 회/요청 | `examiner_node` 스팬 등장 횟수 |
| **파이프라인 성공률** | % | 오류 없이 완주한 트레이스 비율 |

**비용 추정 기준 (2026-06 단가 기준 예시)**

```
gpt-4o        Input: $2.50 / 1M tokens  |  Output: $10.00 / 1M tokens
gpt-4o-mini   Input: $0.15 / 1M tokens  |  Output: $0.60 / 1M tokens
```

특허 1건당 평균 토큰 소비 = (SummaryAgent + ClaimAgent + ExaminerAgent × 재시도 + RewriteAgent)  
→ Phoenix에서 3~5건 테스트 후 실측값으로 갱신 필요

---

### 3-3. EC2 인프라 지표 (AWS CloudWatch)

EC2에서 기본 제공되는 지표(5분 간격, 무료)와 CloudWatch Agent 설치 후 수집 가능한 지표(1분 간격)로 나뉜다.

**EC2 기본 지표 (추가 설정 없음)**

| 지표 | CloudWatch 메트릭 이름 | 경보 기준 |
|------|----------------------|----------|
| **CPU 사용률** | `CPUUtilization` | > 80% 지속 5분 → WARNING |
| **네트워크 입/출력** | `NetworkIn` / `NetworkOut` | 트래픽 급증 시 이상 트래픽 의심 |
| **디스크 읽기/쓰기** | `DiskReadOps` / `DiskWriteOps` | 급증 시 I/O 병목 의심 |
| **상태 체크 실패** | `StatusCheckFailed` | 1 이상 = 즉시 조사 (인스턴스 다운) |

**CloudWatch Agent 설치 후 추가 지표 (권장)**

> EC2 기본 지표에는 메모리·디스크 사용량이 없다. CloudWatch Agent를 설치해야 수집 가능.

| 지표 | CloudWatch 메트릭 이름 | 경보 기준 |
|------|----------------------|----------|
| **메모리 사용률** | `mem_used_percent` | > 85% → WARNING (FastAPI + Phoenix 상주 메모리 고려) |
| **디스크 사용률** | `disk_used_percent` | > 80% → WARNING (로그·SQLite 누적 주의) |
| **Docker 컨테이너 수** | 구조화 로그로 대체 | `/health` 실패 시 재시작 여부 확인 |

**컨테이너 수준 지표 (SSH 접속 후 확인)**

```bash
# EC2 SSH 접속 후
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

### 3-4. 비즈니스 지표 (로그 기반)

구조화 로그(`logging_config.py`)에서 아래 이벤트를 기록해두면 이후 집계 가능

| 이벤트 | 로그 필드 | 의미 |
|--------|----------|------|
| 특허 생성 요청 시작 | `event=pipeline_start, request_id, user_id` | 일 요청량 |
| 파이프라인 완료 | `event=pipeline_complete, duration_ms, request_id` | 완료율, 소요 시간 |
| 파이프라인 실패 | `event=pipeline_error, error_type, agent_name, request_id` | 실패 원인 분류 |
| 심사관 반려 | `event=examiner_reject, iteration, request_id` | 재시도 패턴 |

---

## 4. 관찰 방법 (툴링)

### 4-1. Arize Phoenix — LLM 트레이스 (기존 확정)

**접속**: http://localhost:6006

Phoenix UI에서 할 수 있는 것:

```
Traces 탭
  └─ 트레이스 클릭 → 워터폴 뷰
      ├─ summary_node    [2.1s]  1,234 tokens  gpt-4o-mini
      ├─ claim_node      [8.4s]  3,891 tokens  gpt-4o
      ├─ examiner_node   [3.2s]  1,200 tokens  gpt-4o  → 반려
      ├─ rewrite_node    [6.1s]  2,500 tokens  gpt-4o
      └─ examiner_node   [3.0s]  1,180 tokens  gpt-4o  → 승인

Metrics 탭
  └─ Token Count, Latency, Error Rate 시계열 차트
```

**주요 뷰 사용 방법**

| 목적 | Phoenix 경로 |
|------|-------------|
| 특정 요청 전체 흐름 보기 | Traces → 검색창에 `X-Request-ID` 값 입력 |
| 느린 요청 찾기 | Traces → "Duration" 컬럼 내림차순 정렬 |
| 에러 있는 요청만 보기 | Traces → Filter → Status = Error |
| 모델별 토큰 비교 | Spans → Group by `llm.model_name` |
| 오늘 토큰 소비 합계 | Metrics → Token Count → Time range: Today |

---

### 4-2. 헬스체크 엔드포인트 — 즉각 서비스 상태 확인

**구현 목표**: 각 서비스에 `/health` 엔드포인트를 추가해 "살아있음"을 단일 HTTP 요청으로 확인

**FastAPI `/health` 응답 예시**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "checks": {
    "phoenix_reachable": true,
    "openai_env_set": true
  }
}
```

**Django `/health/` 응답 예시**

```json
{
  "status": "ok",
  "db": "ok"
}
```

**확인 방법**

```bash
# 빠른 상태 확인
curl -s http://localhost:8001/health | python3 -m json.tool
curl -s http://localhost:8000/health/ | python3 -m json.tool

# 컨테이너 전체 한 번에 확인
for port in 8000 8001 6006; do
  echo -n "port $port: "
  curl -sf http://localhost:$port/health 2>/dev/null && echo "OK" || echo "FAIL"
done
```

---

### 4-3. AWS CloudWatch — EC2 인프라 모니터링

#### A. CloudWatch 콘솔 대시보드 구성

1. AWS 콘솔 → CloudWatch → Dashboards → "Create dashboard"
2. 위젯 추가 권장 순서:

```
[Line] CPUUtilization          — EC2 CPU 추이 (1시간, 5분 간격)
[Line] mem_used_percent        — 메모리 사용률 (CloudWatch Agent 필요)
[Number] StatusCheckFailed     — 인스턴스 상태 (0 = 정상)
[Line] NetworkIn / NetworkOut  — 트래픽 입출력
[Line] disk_used_percent       — 디스크 잔여 (로그 누적 모니터링)
```

#### B. CloudWatch Alarm 설정 (권장 최소 3개)

| 알람 이름 | 조건 | 액션 |
|-----------|------|------|
| `patent-cpu-high` | CPUUtilization > 80%, 2연속 5분 | SNS → 이메일 알림 |
| `patent-instance-down` | StatusCheckFailed >= 1 | SNS → 이메일 알림 |
| `patent-disk-full` | disk_used_percent > 80% | SNS → 이메일 알림 |

**SNS 알림 설정 방법**

```
CloudWatch → Alarms → Create alarm
  → Metric: 위 조건 중 하나 선택
  → Actions: Create new SNS topic → 이메일 주소 입력
  → 이메일 수신 후 구독 확인 클릭
```

#### C. CloudWatch Logs — Docker 로그 중앙 수집

docker-compose에 `awslogs` 드라이버를 설정하면 컨테이너 로그가 CloudWatch Logs로 자동 전송된다.

```yaml
# docker-compose.yml 각 서비스에 추가
logging:
  driver: "awslogs"
  options:
    awslogs-region: "ap-northeast-2"        # 서울 리전
    awslogs-group: "/patent-ai/fastapi"     # 서비스별 로그 그룹
    awslogs-stream: "fastapi-worker"
```

로그 그룹 구성 예시:

```
/patent-ai/django        — Django 웹 서버 로그
/patent-ai/fastapi       — FastAPI AI 워커 로그 (에이전트 이벤트 포함)
/patent-ai/phoenix       — Phoenix 컨테이너 로그
```

CloudWatch Logs Insights로 로그 쿼리:

```sql
-- 에러 이벤트 집계 (최근 24시간)
fields @timestamp, agent_name, error_type
| filter levelname = "ERROR"
| stats count(*) by agent_name
| sort count desc

-- 특정 request_id 전체 흐름 추적
fields @timestamp, event, agent_name, duration_ms
| filter request_id = "abc-123"
| sort @timestamp asc
```

#### D. Phoenix UI 접속 방법 (EC2 운영 환경)

Phoenix는 EC2 내부 포트(6006)에서만 동작하므로 외부에서 접속하려면 SSH 터널 사용:

```bash
# 로컬 터미널에서 실행 (EC2_IP는 실제 퍼블릭 IP로 교체)
ssh -L 6006:localhost:6006 -L 8001:localhost:8001 ubuntu@<EC2_IP> -N

# 위 명령 실행 후 로컬 브라우저에서 접속
# Phoenix UI:  http://localhost:6006
# FastAPI docs: http://localhost:8001/docs
```

> **보안 주의**: Phoenix 포트(6006)는 Security Group에서 인터넷(0.0.0.0/0) 오픈 금지. SSH 터널로만 접근.

---

### 4-4. 구조화 로그 — 빠른 임시 분석

`logging_config.py`의 JSON 포맷 로그(`ENV=prod`)를 활용

```bash
# 특정 request_id의 전체 로그 추적
docker logs patent_fastapi_worker 2>&1 | python3 -c "
import sys, json
rid = 'abc-123'  # 찾고 싶은 request_id
for line in sys.stdin:
    try:
        obj = json.loads(line)
        if obj.get('request_id') == rid:
            print(json.dumps(obj, ensure_ascii=False, indent=2))
    except: pass
"

# 에러 이벤트 집계
docker logs patent_fastapi_worker 2>&1 | python3 -c "
import sys, json
from collections import Counter
errors = Counter()
for line in sys.stdin:
    try:
        obj = json.loads(line)
        if obj.get('levelname') == 'ERROR':
            errors[obj.get('agent_name', 'unknown')] += 1
    except: pass
print(errors)
"
```

---

### 4-5. (선택) Prometheus + Grafana — HTTP 서비스 지표 대시보드

CloudWatch가 EC2 시스템 지표를 담당하고, Phoenix가 LLM 지표를 담당하므로,  
HTTP P95 레이턴시·RPS 등 애플리케이션 수준 지표를 시각화하려면 Prometheus + Grafana를 추가한다.  
현 단계에서는 **선택 사항**이며, 운영 사용자가 생기면 도입 권장.

**EC2에서 추가하는 방법**

1. `prometheus-fastapi-instrumentator` 패키지 추가 → FastAPI `/metrics` 엔드포인트 자동 생성
2. `docker-compose.yml`에 `prometheus`(9090)·`grafana`(3001) 서비스 추가
3. EC2 Security Group에서 Grafana 포트(3001)는 팀 IP만 허용
4. Grafana에서 "FastAPI Observability" 커뮤니티 대시보드(ID: 17175) 임포트

```yaml
# docker-compose.yml 추가 예시 (선택)
prometheus:
  image: prom/prometheus:latest
  container_name: patent_prometheus
  ports:
    - "127.0.0.1:9090:9090"   # EC2 외부 노출 금지, 로컬만
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana:latest
  container_name: patent_grafana
  ports:
    - "3001:3000"              # Security Group으로 팀 IP만 허용
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin   # 운영 시 반드시 변경
```

```yaml
# monitoring/prometheus.yml
scrape_configs:
  - job_name: fastapi
    static_configs:
      - targets: ["fastapi-worker:8001"]
```

**EC2 Security Group 설정 (Grafana 접근 제한)**

```
Inbound Rules:
  Port 3001  |  TCP  |  Source: 팀 IP/32   # Grafana
  Port 22    |  TCP  |  Source: 팀 IP/32   # SSH
  Port 80    |  TCP  |  Source: 0.0.0.0/0  # HTTP (서비스)
  # 6006(Phoenix), 9090(Prometheus)는 인바운드 규칙에 추가하지 않음
```

---

## 5. 지표 우선순위 요약

| 우선순위 | 지표 | 도구 | 구현 난이도 |
|---------|------|------|------------|
| **P0 (즉시)** | LLM 트레이스, 토큰 수, 에이전트 레이턴시 | Phoenix (이미 구현) | 완료 |
| **P0 (즉시)** | EC2 CPU·네트워크·상태 체크 | AWS CloudWatch 기본 지표 (자동 수집) | 완료 |
| **P1 (이번 스프린트)** | 헬스체크 `/health` 엔드포인트 | FastAPI + Django 코드 추가 | 낮음 |
| **P1 (이번 스프린트)** | 파이프라인 이벤트 구조화 로그 | `logging_config.py` 활용 | 낮음 |
| **P1 (이번 스프린트)** | EC2 메모리·디스크 지표 + CloudWatch Alarm 3개 | CloudWatch Agent 설치 | 낮음 |
| **P1 (이번 스프린트)** | Docker 로그 → CloudWatch Logs 수집 | docker-compose `awslogs` 드라이버 | 낮음 |
| **P2 (다음 스프린트)** | HTTP P95 레이턴시, RPS 대시보드 | Prometheus + Grafana | 중간 |
| **P3 (선택)** | CloudWatch Logs Insights 쿼리 저장 | AWS 콘솔 | 낮음 |

---

## 6. 구현 계획

### Phase 1: 헬스체크 엔드포인트 추가 (1~2시간)

- [ ] `backend/fastapi/main.py` — `GET /health` 라우터 추가
  - 응답: `{"status":"ok","checks":{"phoenix_reachable":bool,"openai_env_set":bool}}`
- [ ] `backend/django/config/urls.py` — `GET /health/` 뷰 추가
  - 응답: `{"status":"ok","db":"ok"}` (DB ping 포함)

### Phase 2: 비즈니스 이벤트 로깅 (2~3시간)

- [ ] `agents/core/graph.py` (또는 FastAPI 라우터) — 파이프라인 시작/완료/실패 시 구조화 로그 emit
  - 필드: `event`, `request_id`, `duration_ms`, `agent_name`, `error_type` (실패 시)
- [ ] `agents/examiner_agent.py` — 반려 시 `event=examiner_reject, iteration=N` 로그 추가

### Phase 3: AWS CloudWatch 설정 (1~2시간)

- [ ] EC2 IAM Role에 `CloudWatchAgentServerPolicy` 정책 부착
- [ ] EC2 접속 후 CloudWatch Agent 설치 및 설정 파일 작성
  ```bash
  sudo yum install amazon-cloudwatch-agent   # Amazon Linux
  # 또는
  sudo apt install amazon-cloudwatch-agent   # Ubuntu
  ```
- [ ] `docker-compose.yml` 각 서비스에 `awslogs` 로그 드라이버 추가
- [ ] CloudWatch 콘솔에서 대시보드 1개 생성 (CPU, 메모리, 디스크, StatusCheck)
- [ ] CloudWatch Alarm 3개 생성 (CPU > 80%, StatusCheck 실패, 디스크 > 80%)
- [ ] SNS 토픽 생성 → 팀 이메일 구독 등록

### Phase 4: Phoenix 지표 리뷰 루틴 수립 (팀 프로세스)

- [ ] EC2 운영 시 Phoenix 접속은 SSH 터널 사용 (포트 6006 직접 오픈 금지)
  ```bash
  ssh -L 6006:localhost:6006 ubuntu@<EC2_IP> -N
  ```
- [ ] 매일 개발 시작 전 Phoenix UI 접속해 전날 트레이스 이상 유무 확인
- [ ] 주 1회 토큰 소비량 집계 → 비용 추정 시트 갱신
- [ ] 느린 트레이스(P95 기준) 3개 선정 후 원인 분석 → 프롬프트/모델 최적화

### Phase 5: Prometheus + Grafana (선택, 운영 단계)

- [ ] `pyproject.toml`에 `prometheus-fastapi-instrumentator` 추가
- [ ] FastAPI `startup`에서 `Instrumentator().instrument(app).expose(app)` 호출
- [ ] `docker-compose.yml`에 prometheus, grafana 서비스 추가
- [ ] Grafana 대시보드 임포트 및 경보 규칙 설정

---

## 7. 파일 변경 목록

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `backend/fastapi/main.py` | 수정 | `GET /health` 엔드포인트 추가 |
| `backend/django/config/urls.py` | 수정 | `GET /health/` URL 추가 |
| `backend/django/config/views.py` | 수정 또는 신규 | health 뷰 함수 (DB ping 포함) |
| `docker-compose.yml` | 수정 | 각 서비스에 `awslogs` 로그 드라이버 추가 |
| `agents/core/graph.py` | 수정 | 파이프라인 이벤트 구조화 로그 추가 |
| `agents/examiner_agent.py` | 수정 | 반려 이벤트 로그 추가 |
| `monitoring/cloudwatch-agent.json` | 신규 | CloudWatch Agent 수집 설정 (메모리·디스크) |
| `monitoring/prometheus.yml` | 신규 (선택) | Prometheus 스크레이프 설정 |

---

## 8. 승인 기준 (Acceptance Criteria)

1. `curl http://localhost:8001/health` → HTTP 200, `{"status":"ok"}` 반환 (EC2에서는 SSH 터널 또는 내부 IP로 확인)
2. `curl http://localhost:8000/health/` → HTTP 200, `{"status":"ok","db":"ok"}` 반환
3. 특허 생성 요청 1건 후 Phoenix에서 아래 3가지 확인 가능 (SSH 터널: `ssh -L 6006:localhost:6006 ubuntu@<EC2_IP> -N`)
   - 전체 파이프라인 트레이스 (워터폴 뷰)
   - 각 에이전트 노드별 소요 시간
   - 총 토큰 소비량 (prompt + completion)
4. FastAPI 로그에서 `event=pipeline_start`, `event=pipeline_complete` 이벤트 확인
5. ExaminerAgent 반려 시 `event=examiner_reject` 로그 확인
6. AWS CloudWatch 콘솔에서 EC2 인스턴스 CPU·StatusCheck 지표 확인 가능
7. CloudWatch Logs 콘솔에서 `/patent-ai/fastapi` 로그 그룹에 컨테이너 로그 수집 확인
8. CloudWatch Alarm 3개 (CPU, StatusCheck, 디스크) 생성 및 SNS 이메일 알림 수신 확인

---

## 9. 리스크

| 리스크 | 완화 방안 |
|--------|-----------|
| Phoenix 지표 보존 기간 제한 (기본 메모리 기반) | SQLite 볼륨 마운트 추가로 재시작 후에도 데이터 유지 |
| Phoenix/Prometheus 포트 외부 노출 | Security Group에서 6006, 9090 인바운드 규칙 추가 금지 — SSH 터널로만 접근 |
| EC2 메모리 지표 기본 미수집 | CloudWatch Agent 미설치 시 메모리 모니터링 불가 → P1 우선순위로 설치 |
| CloudWatch Logs 비용 증가 | 로그 보존 기간 설정 (권장: 30일), 불필요한 DEBUG 로그는 프로덕션에서 INFO로 제한 |
| EC2 인스턴스 타입 부족 (메모리) | Phoenix + FastAPI 동시 상주 시 최소 t3.medium (4GB) 권장 — `mem_used_percent` 알람으로 조기 감지 |
| 구조화 로그 필드 불일치 | `event`, `request_id`, `duration_ms` 필드명을 팀 컨벤션으로 문서화 |
| Phoenix 데이터 프라이버시 | 프롬프트 내용에 개인정보 포함 가능 → 운영 환경에서 `PHOENIX_DISABLE_PAYLOAD_CAPTURE=true` 설정 |
| awslogs 드라이버 권한 오류 | EC2 IAM Role에 `logs:CreateLogGroup`, `logs:PutLogEvents` 권한 포함 여부 확인 |
| `sqlite_data` 볼륨 잔재 | `docker-compose.yml`에 선언된 `sqlite_data` 볼륨은 어떤 서비스도 사용하지 않음 → 혼란 방지를 위해 제거 권장 |

---

## 10. 스케일링 전략

### 오토스케일링은 자동으로 되지 않는다

AWS EC2 Auto Scaling은 **설정이 필요한 기능**이며, 단순히 CloudWatch Alarm을 켠다고 인스턴스가 자동으로 늘어나지 않는다.  
작동 구조는 다음과 같다:

```
CloudWatch Alarm (CPU > 80% 지속)
        ↓ 트리거
Auto Scaling Group (사전 설정 필요)
        ↓ 새 인스턴스 시작
EC2 인스턴스 추가 (동일 AMI 복제)
        ↓
Application Load Balancer가 트래픽 분산
```

필요한 사전 설정: EC2 AMI 스냅샷, Launch Template, Auto Scaling Group, ALB — 설정 난이도가 높다.

---

### 현재 아키텍처에서 오토스케일링이 바로 안 되는 이유

현재 구조(단일 EC2 + Docker Compose)를 그대로 수평 확장하면 다음 문제가 발생한다.

| 문제 | 원인 | 현재 상태 |
|------|------|----------|
| **PostgreSQL 위치** | DB가 같은 EC2 안에 있으면 인스턴스 2대가 각자 다른 DB를 바라봄 | ✅ RDS 사용 중 — 해결됨 |
| **Django 세션 불일치** | 세션이 DB에 저장되어 인스턴스 간 공유 안 됨 | ✅ RDS 공유 → 자동 해결됨 |
| **Phoenix 트레이스 분산** | 인스턴스마다 Phoenix가 따로 떠서 트레이스가 나뉘어 저장됨 | ❌ 유일한 남은 블로커 |

**RDS를 이미 사용 중이므로 Scale Out의 남은 블로커는 Phoenix 하나뿐이다.**

---

### 현실적인 스케일링 선택지

#### 단기 (현재 단계): Scale Up — 인스턴스 업그레이드

설정 없이 바로 적용 가능한 가장 빠른 방법.

| 인스턴스 타입 | vCPU | 메모리 | 월 비용 (서울) | 적합한 상황 |
|-------------|------|--------|-------------|-----------|
| t3.small    | 2    | 2 GB   | ~$15        | 개발·테스트 |
| **t3.medium** | **2** | **4 GB** | **~$30** | **현재 권장 최소** |
| t3.large    | 2    | 8 GB   | ~$60        | FastAPI + Phoenix 메모리 여유 필요 시 |
| t3.xlarge   | 4    | 16 GB  | ~$120       | 동시 요청 증가 시 |

> CloudWatch의 `mem_used_percent` 알람(> 85%)이 울리면 한 단계 위 타입으로 올리는 것이 Scale Out보다 훨씬 간단하다.

**인스턴스 타입 변경 방법 (다운타임 ~2분)**

```bash
# 1. EC2 콘솔 → 인스턴스 중지
# 2. Actions → Instance Settings → Change Instance Type
# 3. 새 타입 선택 후 저장
# 4. 인스턴스 시작
```

---

#### 장기 (사용자가 늘어날 때): Scale Out 준비 조건

수평 확장을 하려면 아래 순서로 아키텍처를 먼저 확인·정비해야 한다.

```
1단계: PostgreSQL RDS 외부화 ✅ 완료
  └─ 이미 RDS 사용 중 → 여러 EC2 인스턴스가 동일 DB를 바라봄

2단계: Django 세션 ✅ 완료
  └─ RDS 공유로 세션도 자동으로 인스턴스 간 공유됨

3단계: Phoenix → 별도 인스턴스 또는 Phoenix Cloud 분리  ← 현재 블로커
  └─ AI 워커 인스턴스를 늘리면 각각 Phoenix가 떠서 트레이스가 분산됨
  └─ 해결책: Phoenix를 독립 EC2에 분리하거나 Phoenix Cloud 사용

4단계: Auto Scaling Group + ALB 설정
  └─ 3단계 완료 후 바로 적용 가능
```

---

### Phoenix 별도 EC2 분리 방안

Scale Out의 유일한 남은 블로커인 Phoenix를 독립 인스턴스로 분리하는 구체적인 방법.

#### 목표 아키텍처

```
[ 인터넷 ]
     │
     ▼
Application Load Balancer
     │
     ├──────────────────────────────┐
     ▼                              ▼
EC2 #1 (앱 서버)          EC2 #2 (앱 서버)
  Django   :8000             Django   :8000
  FastAPI  :8001             FastAPI  :8001
     │  OTLP                    │  OTLP
     └──────────┬───────────────┘
                ▼
        EC2 #3 (Phoenix 전용)
          Phoenix  :6006
          (트레이스 중앙 수집)

                RDS PostgreSQL  ←  Django DB 공유
```

---

#### 분리 절차

**Step 1: Phoenix 전용 EC2 생성**

```
AWS 콘솔 → EC2 → Launch Instance
  AMI:           Ubuntu 24.04 LTS
  Instance type: t3.small (2GB — Phoenix 단독 실행 시 충분)
  Security Group:
    - 인바운드 6006 (Phoenix UI)  → 앱 서버 EC2 보안 그룹 ID만 허용
    - 인바운드 4317 (OTLP gRPC)   → 앱 서버 EC2 보안 그룹 ID만 허용
    - 인바운드 22   (SSH)         → 팀 IP만 허용
    - 인터넷(0.0.0.0/0) 허용 없음
```

**Step 2: Phoenix 전용 EC2에 Docker 설치 및 실행**

```bash
# EC2 SSH 접속 후
sudo apt update && sudo apt install -y docker.io
sudo systemctl enable docker && sudo systemctl start docker

# Phoenix 실행 (데이터 영구 보존 볼륨 포함)
sudo docker run -d \
  --name patent_phoenix \
  --restart unless-stopped \
  -p 6006:6006 \
  -p 4317:4317 \
  -v phoenix_data:/data \
  -e PHOENIX_WORKING_DIR=/data \
  arizephoenix/phoenix:latest
```

**Step 3: 앱 서버의 Phoenix 엔드포인트 변경**

```dotenv
# .env (앱 서버 EC2)
# 기존
PHOENIX_COLLECTOR_ENDPOINT=http://phoenix:6006/v1/traces

# 변경 — Phoenix EC2의 프라이빗 IP 사용 (퍼블릭 IP 사용 금지)
PHOENIX_COLLECTOR_ENDPOINT=http://<Phoenix_EC2_Private_IP>:6006/v1/traces
```

> 같은 VPC 안에 있으면 프라이빗 IP로 통신 가능. 퍼블릭 IP는 비용 발생 + 보안 위험.

**Step 4: 앱 서버 docker-compose에서 phoenix 서비스 제거**

```yaml
# docker-compose.yml — phoenix 서비스 블록 삭제
# 아래 내용 제거:
# phoenix:
#   image: arizephoenix/phoenix:latest
#   ports:
#     - "6006:6006"
#     - "4317:4317"
```

**Step 5: 동작 확인**

```bash
# 앱 서버 EC2에서 Phoenix로 연결 확인
curl -s http://<Phoenix_EC2_Private_IP>:6006/health

# FastAPI 재시작 후 트레이스 1건 전송
docker compose restart fastapi-worker

# Phoenix UI 접속 (SSH 터널 — Phoenix EC2 경유)
ssh -L 6006:localhost:6006 ubuntu@<Phoenix_EC2_IP> -N
# 브라우저: http://localhost:6006
```

---

#### 분리 후 비용

| 항목 | 비용 |
|------|------|
| Phoenix 전용 t3.small | ~$15/월 |
| 동일 VPC 내 프라이빗 통신 | $0 (데이터 전송 무료) |
| Phoenix 볼륨 (gp3 20GB) | ~$1.6/월 |
| **합계** | **~$17/월** |

---

#### 분리 완료 후 Auto Scaling Group 설정 순서

```
1. 앱 서버 EC2를 AMI로 스냅샷
2. Launch Template 생성 (AMI + 인스턴스 타입 + .env 경로 지정)
3. Auto Scaling Group 생성
     - 최소 1대, 최대 3대
     - 스케일 아웃 조건: CPU > 70% 5분 지속
     - 스케일 인 조건:  CPU < 30% 10분 지속
4. Application Load Balancer 생성
     - 타겟 그룹: Auto Scaling Group
     - 헬스체크 경로: /health (Django :8000, FastAPI :8001 각각)
5. CloudWatch Alarm과 Auto Scaling Action 연결
```

---

### 스케일링 의사결정 기준

```
CloudWatch CPU > 80% 알람 발생
        │
        ├─ 일시적 급증? (수 분)
        │      → 무시 또는 관망
        │
        ├─ 지속적 (30분 이상)?
        │      → t3.large로 Scale Up (즉시 적용, 다운타임 ~2분)
        │
        └─ Scale Up 후에도 반복?
               → Phoenix 분리 → Auto Scaling Group 구성 (Scale Out)
```