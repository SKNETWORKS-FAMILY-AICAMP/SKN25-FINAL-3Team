# CLAUDE.md — 특허 명세서 자동 작성 서비스

> 코딩 에이전트(Claude Code)가 이 프로젝트에서 작업할 때 가장 먼저 읽는 파일입니다.
> 모든 맥락, 규칙, 인터페이스 요약이 여기에 있습니다.

---

## 1. 프로젝트 개요

발명가(또는 변리사)가 **챗봇 UI를 통해 대화**하며 기술을 설명하면, 특허법적 요건에 맞는 정식 특허 명세서를 자동 생성하는 AI 서비스입니다.

### 핵심 사용자 흐름

```
① 사용자 ↔ 상담 챗봇 (멀티턴 대화)
      - 발명 내용을 자연어로 설명
      - AI가 부족한 정보를 추가 질문
      - 충분한 정보가 모이면 상담 종료
              ↓
② 명세서 자동 생성 파이프라인 실행
      - 병렬: 선행기술조사 + 청구항 초안 작성
      - 심사 → (필요 시) 청구항 재작성
      - 도면 생성 → 명세서 본문 작성
              ↓
③ 사용자에게 완성된 명세서 제공 (UI에서 확인·다운로드)
```

> **중요**: 상담 단계(①)는 단일 API 호출이 아닌 **여러 번의 메시지를 주고받는 대화형** 흐름입니다.
> 세션 단위로 대화 이력을 유지하며, `session_id`로 연속적인 대화를 식별합니다.

**핵심 Tech Stack**

| 레이어 | 기술 |
|---|---|
| 에이전트 오케스트레이션 | LangGraph 0.2+ |
| LLM | OpenAI GPT (langchain-openai) |
| API 서버 | FastAPI + Uvicorn |
| 프로토타입 UI | Streamlit (`app.py`) |
| 백엔드(예정) | Django 5 |
| 패키지 관리 | uv (pyproject.toml) |
| 테스트 | pytest + pytest-asyncio |
| 린터 | ruff (line-length=100) |
| Python | 3.11+ (`.python-version` 참조) |

---

## 2. 에이전트 파이프라인

### Phase 1 — 상담 챗봇 (멀티턴, UI와 직접 연동)

```
사용자 메시지 전송
    │
    ▼
[consulting 노드] ──→ is_consultation_done?
    │                      │
    │ NO (추가 질문 필요)   │ YES (정보 충분)
    ↓                      ↓
AI 질문 메시지 반환     Phase 2 파이프라인 실행
    │
    ▼
사용자에게 표시 → 다시 메시지 전송 (반복)
```

### Phase 2 — 명세서 생성 파이프라인 (자동 실행)

```
consulting 완료 (is_consultation_done=True)
    │
    ├──→  [patent_search]  ──→  END   (선행기술조사, 병렬 브랜치)
    │
    └──→  [claims]  ──→  [examiner]
                               │
                    ┌──(등록불가 & 재시도<2)──┐
                    │                         │
                    ▼                         │
               [drawing]  ←────────────────── ┘
                    │
                    ▼
             [description]
                    │
                    ▼
                  END  →  UI에 명세서 표시
```

**Phase 1 루프**: `consulting` 노드는 `is_consultation_done=False`를 반환해 대화를 계속 이어갑니다.
`is_consultation_done=True`가 되면 Phase 2로 자동 전환됩니다.

**Phase 2 재시도 루프**: `examiner`가 등록 불가 판정 시 `claims`로 되돌아가 청구항을 재작성합니다. 최대 `MAX_REVISION = 2`회 (`agents/graph.py`).

### 세션 관리 원칙

- 각 사용자의 대화는 `session_id`로 식별합니다.
- `raw_conversation` 필드에 전체 대화 이력을 누적합니다.
- Phase 1 중 서버 재시작이 있어도 대화가 이어질 수 있도록, DB에 세션 상태를 저장합니다.
- 상세 설계: `docs/decisions/003-multiturn-session.md` 참조.

---

## 3. 모듈 맵 (파일별 한 줄 요약)

### agents/
| 파일 | 역할 |
|---|---|
| `agents/state.py` | 전체 파이프라인 공유 상태 `PatentAgentState` (TypedDict) |
| `agents/graph.py` | LangGraph 그래프 정의, 엣지/조건부 라우터 |
| `agents/nodes/consulting.py` | 발명 요소 추출 노드 (현재 mock) |
| `agents/nodes/patent_search.py` | KIPRIS 선행기술 검색 노드 (현재 mock) |
| `agents/nodes/claims.py` | 청구항 생성 노드 (현재 mock) |
| `agents/nodes/examiner.py` | 청구항 심사 노드 (현재 mock) |
| `agents/nodes/drawing.py` | Mermaid 도면 생성 노드 (현재 mock) |
| `agents/nodes/description.py` | 명세서 본문 생성 노드 (현재 mock) |
| `agents/tools/document_utils.py` | PDF·DOCX·HWP 파싱 유틸 |
| `agents/tools/kipris_api.py` | KIPRIS Open API 래퍼 (미구현) |

### api/
| 파일 | 역할 |
|---|---|
| `api/main.py` | FastAPI 앱 진입점 |
| `api/routers/*.py` | 노드별 HTTP 엔드포인트 (`POST /consult` 등) |
| `api/schemas/patent.py` | Pydantic 요청·응답 스키마 |

### 기타
| 파일 | 역할 |
|---|---|
| `app.py` | Streamlit 프로토타입 진입점 |
| `backend/services/agent_client.py` | Django → FastAPI 호출 클라이언트 |
| `tests/` | pytest 테스트 (api/, agents/, fixtures/) |
| `docs/` | 아키텍처·인터페이스·컨벤션 문서 |
| `data/` | 특허 PDF 원본 데이터 |

---

## 4. 실행 방법

### 환경 설정
```bash
cp .env.example .env
# .env에 OPENAI_API_KEY, KIPRIS_API_KEY 등 입력
```

### Streamlit 프로토타입
```bash
uv run streamlit run app.py
```

### FastAPI 에이전트 서버
```bash
uv run uvicorn api.main:app --reload --port 8001
```

### 테스트
```bash
uv run pytest                          # 전체
uv run pytest tests/agents/            # 에이전트 노드 단위 테스트
uv run pytest tests/api/               # API 통합 테스트
uv run pytest -v --tb=short            # 상세 출력
```

### 린트
```bash
uv run ruff check .
uv run ruff format .
```

---

## 5. 핵심 인터페이스 요약

> 상세 명세는 `docs/interfaces/` 참조.

### PatentAgentState (agents/state.py)
모든 노드는 `PatentAgentState` TypedDict를 입력받아 **변경된 필드만 dict로 반환**합니다.

```python
def run(state: PatentAgentState) -> dict:
    ...
    return {"필드명": 값}  # 전체 state가 아닌 변경분만 반환
```

#### 멀티턴 대화 관련 핵심 필드

| 필드 | 타입 | 설명 |
|---|---|---|
| `raw_conversation` | `list` | 전체 대화 이력 (LangGraph `add_messages`로 자동 누적) |
| `next_question` | `str` | consulting 노드가 사용자에게 반환할 다음 질문 |
| `is_consultation_done` | `bool` | `True`이면 Phase 2(명세서 생성) 파이프라인으로 전환 |

> `is_consultation_done` 필드는 `agents/state.py`에 아직 없습니다.
> consulting 노드 구현 시 팀 합의 후 추가하세요. (`graph.py` 라우터 동시 수정 필요)

### 노드 함수 시그니처 (고정)
```python
# agents/nodes/모든노드.py
def run(state: PatentAgentState) -> dict: ...
```

### 노드별 입출력 계약
| 노드 | 주요 입력 필드 | 주요 출력 필드 |
|---|---|---|
| consulting | `user_input` | `invention_flow`, `problem`, `differentiation`, `effect`, `raw_conversation` |
| patent_search | `invention_flow`, `problem` | `similar_patents`, `ipc_codes` |
| claims | `invention_flow`, `differentiation`, `effect` | `claims` |
| examiner | `claims` | `is_registerable`, `examiner_opinion`, `examiner_issues`, `revision_count` |
| drawing | `claims` | `flowchart_code`, `system_diagram_code` |
| description | `invention_flow`, `problem`, `differentiation`, `effect`, `flowchart_code` | `background`, `problem_statement`, `solution`, `drawing_description`, `detailed_description` |

---

## 6. 컨벤션 & 필수 규칙

> 전체 컨벤션은 `docs/conventions.md` 참조.

### 절대 규칙

1. **`agents/state.py` 단독 수정 금지** — State 필드 추가/삭제 시 반드시 팀 합의 후, `graph.py`도 함께 수정.
2. **노드 함수 시그니처 변경 금지** — 항상 `def run(state: PatentAgentState) -> dict`.
3. **KIPRIS API 직접 호출 금지** — 반드시 `agents/tools/kipris_api.py`를 통해 호출.
4. **PR 전 `pytest` 통과 필수** — 실패 상태로 PR 금지.
5. **mock 코드는 `# ── mock ──` 주석 블록 유지** — 실제 구현으로 교체 시 주석 블록 제거.

### 새 노드 추가 시 체크리스트
- [ ] `agents/nodes/새노드.py` — `run(state)` 함수 구현
- [ ] `agents/state.py` — 출력 필드 추가 (팀 합의 후)
- [ ] `agents/graph.py` — `add_node()` + `add_edge()` 추가
- [ ] `agents/nodes/__init__.py` — import 추가
- [ ] `api/routers/새노드.py` — FastAPI 라우터 추가
- [ ] `tests/agents/test_새노드.py` — 단위 테스트 작성
- [ ] `docs/interfaces/새노드.md` — 인터페이스 문서 작성

### 코딩 스타일
- 타입 힌트 필수 (모든 함수 매개변수·반환값)
- 라인 길이 최대 100자 (ruff 설정)
- docstring: 한국어 또는 영어 모두 허용, 역할/입력/출력 명시
- 모든 외부 API 호출은 `try/except` 처리

---

## 7. 브랜치 전략

```
main          ← 배포 브랜치, 직접 push 금지
epic          ← 기능 브랜치 통합
feature/이름-작업내용  ← 개인 작업 브랜치
fix/이름-수정내용
```

상세 규칙: `BRANCH_RULES.md` 참조.

---

## 8. 현재 구현 상태 (2026-05)

| 노드 | 상태 | 담당 브랜치 |
|---|---|---|
| consulting | 🔴 mock | consulting |
| patent_search | 🔴 mock | — |
| claims | 🔴 mock | — |
| examiner | 🔴 mock | — |
| drawing | 🔴 mock | — |
| description | 🔴 mock | — |
| kipris_api.py | 🔴 미구현 | — |
| FastAPI 라우터 | 🟡 뼈대 있음 | — |
| Django 백엔드 | 🟡 계획중 | — |

> 노드 구현 완료 시 이 표를 🟢로 업데이트하세요.

---

## 9. 참고 문서

- `docs/architecture.md` — 전체 시스템 아키텍처 설계
- `docs/conventions.md` — 상세 코딩 컨벤션
- `docs/interfaces/` — 노드별 Input/Output 계약 상세
- `docs/decisions/` — 아키텍처 결정 기록 (ADR)
- `BRANCH_RULES.md` — Git 브랜치·PR 규칙
- `.env.example` — 환경변수 목록
