# ADR-003: Redis를 파이프라인 진행상황 추적 전용으로 사용

**상태:** Accepted  
**날짜:** 2026-06-02

## 맥락

파이프라인 실행 중 "현재 어떤 agent가 실행 중인가"를 클라이언트에 전달하는 방법이 필요했다.

후보:
1. PostgreSQL `patent_runs` 테이블에 `current_agent` 컬럼 추가
2. Redis에 TTL 키로 저장
3. WebSocket / SSE로 실시간 push

## 결정

Redis에 `run:{run_id}:agent` 키로 현재 실행 중인 agent 이름을 TTL 1일로 저장한다.  
클라이언트는 `GET /api/runs/{run_id}` 폴링 시 Redis 값을 함께 읽어 `current_agent`로 반환받는다.

```
파이프라인 실행 중:
  Redis SET run:{run_id}:agent "prior_art" EX 86400

GET /api/runs/{run_id} 응답:
  { "status": "running", "current_agent": "prior_art", ... }
```

## 이유

- **DB 부하 분리**: agent 전환마다 PostgreSQL에 write하면 파이프라인 실행 중 불필요한 DB 쓰기가 발생한다. Redis는 in-memory이므로 빠르고 부하가 없다.
- **내구성 불필요**: 진행상황은 일시적인 정보다. 파이프라인이 끝나면 의미가 없으므로 TTL로 자동 만료되는 것이 적절하다.
- **장애 허용**: Redis 장애 시에도 파이프라인은 계속 실행된다 (`current_agent` 응답이 `null`이 될 뿐). 코드에서 Redis 예외를 무시 처리한다.

## 결과

- Redis는 캐시/진행상황 용도로만 쓰고, 최종 결과는 반드시 PostgreSQL에 저장한다.
- Redis 데이터는 재시작 시 초기화된다 (영속성 설정 없음).
- 향후 실시간 스트리밍이 필요해지면 WebSocket/SSE로 교체할 수 있다. Redis 의존성은 `fastapi/app/routers/` 레이어에만 있어 교체 범위가 좁다.
