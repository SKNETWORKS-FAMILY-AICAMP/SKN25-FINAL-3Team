# ADR-004: Agent output 검증 실패 시 명시적 중단 (silent failure 제거)

**상태:** Accepted  
**날짜:** 2026-06-02

## 맥락

LLM agent가 잘못된 형식의 JSON을 반환했을 때 파이프라인이 어떻게 동작해야 하는지 결정이 필요했다.

이전 방식은 검증 실패 시 빈 dict나 fallback 값을 반환하고 파이프라인을 계속 진행했다 (silent failure).

## 결정

검증 실패 시 `AgentValidationError`를 발생시켜 파이프라인을 즉시 중단한다.  
단, `ENABLE_LLM_REPAIR=true` 환경변수가 설정된 경우에는 LLM repair를 1회 시도한 뒤 재검증한다.

```
raw_output
  → normalize_to_schema_shape()   # 흔한 형식 오류 사전 교정
  → Pydantic model_validate()
  → 실패 + ENABLE_LLM_REPAIR=true → repair_agent_output_with_llm() → 재검증
  → 그래도 실패 → AgentValidationError → 파이프라인 중단
```

repair는 형식 정규화(필드명/타입/구조 교정)만 수행하고, 특허 내용을 새로 만들거나 개선하지 않는다.

## 이유

- **특허 문서의 특성**: 청구항·명세서에서 빈 필드나 잘못된 구조가 다음 agent로 넘어가면 최종 출력물이 조용히 훼손된다. 발견이 늦어질수록 디버깅 비용이 커진다.
- **실패 가시성**: `AgentValidationError`는 `patent_runs.errors`에 기록되고 API 응답에 노출된다. 어떤 agent가 왜 실패했는지 즉시 알 수 있다.
- **개별 재실행**: 실패한 agent는 `POST /api/agents/{agent_name}/run`으로 단독 재실행할 수 있어 전체 파이프라인을 처음부터 다시 돌릴 필요가 없다.

## 결과

- 파이프라인 실패율이 올라가 보일 수 있으나, 이전에 조용히 넘어가던 실패가 드러나는 것이다.
- LLM repair 모델은 기본값 `gpt-4o-mini`로 형식 교정에만 사용하며 고성능 모델이 필요하지 않다 (`AGENT_REPAIR_MODEL` 환경변수로 변경 가능).
- repair를 끄려면 `ENABLE_LLM_REPAIR=false`(기본값)로 두면 된다.
