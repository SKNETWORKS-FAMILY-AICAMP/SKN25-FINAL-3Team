# 특허 Agent 서비스 배포 구조

이 문서는 개발자 로컬 실행용이 아니라, 발표/배포 서버에서 어떤 프로세스가 어떤 책임을 갖는지 맞추기 위한 기준이다.

## 결론

PR의 초점은 “코드 폴더 정리”가 아니라 아래 4개 경계다.

1. 배포 서버 구조
2. 서버 간 API 연결
3. agent 실행 책임
4. storage/session lifecycle

## 권장 배포 단위

```text
Browser / React UI
  -> Product Backend 또는 API Gateway
  -> patent-api container
       - FastAPI route
       - Master Router
       - LangGraph/service graph
       - agent adapters
       - agent worker logic
  -> Postgres
       - run/session/message/step/artifact/state_snapshot
  -> Redis
       - queue/progress/cache/lock
       - durable 결과 저장소로 쓰지 않음
  -> Object/File Storage
       - PDF/DOCX/HTML/SVG/JSON artifact
```

## Docker와 연결한 서비스 관점

`Dockerfile`은 `patent-api`를 하나의 배포 가능한 서비스로 만든다.

```text
container entrypoint
  uvicorn backend.fastapi.app.main:app

health check
  GET /health

external API
  POST /api/pipeline/run
  POST /api/pipeline/continue
```

`docker-compose.yml`은 개발 편의용 compose가 아니라 서버에서 필요한 런타임 구성 기준이다.

```text
patent-api  = agent orchestration API
postgres    = durable session/storage DB
redis       = queue/progress/cache/lock
volumes     = artifacts/data persistence
```

## 서버 간 API 연결 기준

프론트나 제품 백엔드는 개별 agent를 직접 호출하지 않는다.

```text
Frontend/Product Backend
  -> /api/pipeline/run
  -> /api/pipeline/continue
  -> /api/runs/{run_id}
```

FastAPI 내부에서만 다음을 호출한다.

```text
API router
  -> Master Router
  -> Graph
  -> Adapter
  -> Agent
  -> Pydantic schema validation
  -> state bucket 저장
```

## 현재 `/run` 구현 범위

현재 `/api/pipeline/run`은 `asyncio.to_thread()`로 동기 pipeline을 별도 스레드에서 실행한다.
이 방식은 FastAPI 이벤트 루프 차단을 줄이지만, **백그라운드 큐는 아니다.**
즉 요청자는 agent 실행이 끝날 때까지 기다린 뒤 응답을 받는다.

운영형 구조에서는 이후 PR에서 아래처럼 바꾼다.

```text
POST /api/pipeline/run
  -> run_id 즉시 반환(status=queued)

worker queue
  -> agent pipeline 백그라운드 실행

GET /api/runs/{run_id}
  -> 진행상태/결과 조회
```

## agent 실행 책임

| Layer | 책임 |
| --- | --- |
| FastAPI router | 외부 요청 수신, run_id 생성/조회, 응답 shape 유지 |
| Master Router | 입력 충분성 판단, 다음 agent 선택, follow-up 질문 생성 |
| Graph | 실행 순서, partial rerun, skip/retry 흐름 |
| Adapter | state -> agent input 변환, output schema 검증, dict 저장 |
| Agent | LLM/DB/search/drafting 등 실제 작업 |
| Schema | agent output 계약의 단일 기준 |
| State | graph 실행 중 공유 컨테이너 |

## 현재 구현된 storage/session 범위

이번 PR에서 1차로 구현된 범위:

```text
POST /api/pipeline/run
  -> PostgreSQL patent_runs 생성(status=running)
  -> pipeline 실행
  -> Redis run:{run_id}:agent에 현재 agent 기록
  -> PostgreSQL patent_runs.state/errors/status 최종 업데이트

GET /api/runs/{run_id}
  -> PostgreSQL에 저장된 run/state/errors 조회
  -> 실행 중이면 Redis current_agent 참고
```

아직 구현하지 않은 범위:

```text
- step별 별도 테이블(run_steps)
- artifact 별도 테이블/스토리지 업로드
- /api/runs/{run_id}/steps
- /api/runs/{run_id}/artifacts
- /run 즉시 반환 + worker queue 실행
```

## storage/session lifecycle

최소 lifecycle은 아래 순서로 고정한다.

```text
1. run 생성
   - run_id
   - user_id/session_id optional
   - status=created

2. 입력 저장
   - user_input
   - uploaded document links
   - selected task_type/requested_agents

3. master 판단 저장
   - missing_inputs
   - follow_up_questions
   - route
   - requires_user_input

4. step 실행 저장
   - step_id
   - agent_name
   - status=running/succeeded/failed/skipped
   - started_at/completed_at
   - warnings/details

5. agent output 저장
   - Pydantic 검증 성공 결과: JSON dict
   - 검증 실패 시 AgentValidationError로 중단하고 errors에 원인 기록

6. artifact 저장
   - HTML/DOCX/PDF/SVG/JSON은 파일/object storage에 저장
   - DB/state에는 path/url/metadata만 저장

7. 완료/재실행
   - final_package 생성
   - 특정 step부터 partial rerun 가능
```

## 다음 코드 PR에서 필요한 구현

이 PR은 Docker/service topology 기준을 세우는 PR이다. 다음 구현 PR은 아래를 붙이면 된다.

```text
backend/fastapi/app/models.py or storage.py
  - run/session/step/artifact 저장소 인터페이스

backend/fastapi/app/routers/runs.py
  - GET /api/runs/{run_id}
  - GET /api/runs/{run_id}/steps
  - GET /api/runs/{run_id}/artifacts

agents/graph.py
  - step 단위 status/progress hook
  - partial rerun entrypoint

worker queue
  - Redis/RQ/Celery 중 하나 선택
  - 긴 agent 실행을 API request thread에서 분리
```

## PR 분리 원칙

- schema/state 중복 제거 PR: 작게 유지
- Docker/service topology PR: 배포 구조와 책임 경계만 명확히
- storage/session 구현 PR: DB schema/API 구현
- queue/worker PR: 긴 agent 실행 분리

이렇게 나눠야 발표 때도 “지금 PR이 뭘 해결하는지”가 헷갈리지 않는다.
