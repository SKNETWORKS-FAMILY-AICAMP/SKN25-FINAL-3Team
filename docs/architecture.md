# 시스템 아키텍처 설계문서

> 특허 명세서 자동 작성 서비스 — 멀티 에이전트 통합 구조

---

## 1. 프로젝트 개요

발명가(또는 변리사)가 일상 언어로 기술을 설명하면, 특허법적 요건(신규성·진보성·기재불비 방지)에 맞는 정식 명세서를 자동 생성하는 AI 서비스.

---

## 2. 미결 설계 결정 사항

본 문서를 확정하기 전에 아래 두 가지를 먼저 결정해야 합니다.

### 2-1. 백엔드 구성

| 옵션 | 구성 | 장점 | 단점 |
|---|---|---|---|
| **A. Django 단일** | Django (인증 + 에이전트 호출 모두 처리) | 구성 단순, 러닝커브 낮음 | 에이전트 API 분리가 어려워 확장성 제한 |
| **B. Django + FastAPI** | Django (인증·UI) + FastAPI (에이전트 API 서버) | 에이전트 레이어 독립적으로 확장 가능, async 처리 용이 | 서버 두 개 운영, 팀 러닝커브 |

### 2-2. 에이전트 구현 방식

| 옵션 | 방식 | 장점 | 단점 |
|---|---|---|---|
| **A. 개별 구현** | 각 에이전트를 순수 Python 클래스로 직접 구현 | 의존성 최소화, 동작 완전 제어 | 에이전트 간 상태 관리·오케스트레이션 직접 구현 필요 |
| **B. 에이전트 프레임워크** | LangGraph / LangChain / LlamaIndex 등 활용 | 오케스트레이션·메모리·툴 호출 지원 내장 | 프레임워크 추상화로 디버깅 어려울 수 있음 |

> 위 두 결정이 완료되면 섹션 3(디렉토리 구조)과 섹션 6(통합 방식)을 확정합니다.

---

## 3. 목표 디렉토리 구조

### 옵션 A + A — Django 단일 + 개별 구현

```
SKN25-FINAL-3Team/
│
├── backend/                        # Django 웹 백엔드 (인증·UI·에이전트 호출 모두)
│   ├── config/                     # 프로젝트 설정 (settings.py, urls.py)
│   ├── accounts/                   # 회원 인증 (로그인·회원가입)
│   ├── workspace/                  # 대시보드, 특허 프로젝트 관리
│   ├── core/                       # 홈 화면
│   ├── templates/
│   ├── static/
│   └── manage.py
│
├── agents/                         # AI 에이전트 모듈 (순수 Python 클래스)
│   ├── consulting/                 # Consulting Agent
│   │   ├── consultation_agent.py
│   │   └── document_utils.py
│   ├── patent_search/              # Patent Search Agent
│   │   └── patent_search_agent.py
│   ├── claims/                     # Claims Agent
│   │   └── claims_agent.py
│   ├── examiner/                   # Examiner Agent
│   │   └── examiner_agent.py
│   ├── drawing/                    # Drawing Agent
│   │   ├── drawing_agent.py
│   │   └── claim_to_flowchart.py
│   └── description/                # Description Agent
│       └── description_agent.py
│
├── app.py                          # Streamlit 진입점 (프로토타입)
├── docs/
│   ├── concept.md
│   └── architecture.md
├── data/
│   └── patents/                    # 특허 PDF 원본 데이터
└── requirements.txt
```

---

### 옵션 B + B — Django + FastAPI + 에이전트 프레임워크 (LangGraph)

```
SKN25-FINAL-3Team/
│
├── backend/                        # Django (인증·UI만 담당)
│   ├── config/
│   ├── accounts/
│   ├── workspace/
│   ├── core/
│   ├── templates/
│   ├── static/
│   └── manage.py
│
├── api/                            # FastAPI (에이전트 API 서버)
│   ├── main.py                     # FastAPI 앱 진입점
│   ├── routers/                    # 엔드포인트 라우터
│   │   ├── consulting.py           # POST /consult
│   │   ├── patent_search.py        # POST /patent-search
│   │   ├── claims.py               # POST /claims
│   │   ├── examiner.py             # POST /examine
│   │   ├── drawing.py              # POST /drawing
│   │   └── description.py          # POST /description
│   └── schemas/                    # Pydantic 요청·응답 스키마
│       └── patent.py
│
├── agents/                         # LangGraph 기반 에이전트
│   ├── graph.py                    # 전체 파이프라인 그래프 정의
│   ├── state.py                    # 공유 상태 (PatentAgentState)
│   ├── nodes/                      # 각 에이전트 노드 함수
│   │   ├── consulting.py
│   │   ├── patent_search.py
│   │   ├── claims.py
│   │   ├── examiner.py
│   │   ├── drawing.py
│   │   └── description.py
│   └── tools/                      # 에이전트가 호출하는 툴
│       ├── document_utils.py       # PDF·DOCX·HWP 파싱
│       └── kipris_api.py           # 특허 DB 검색
│
├── app.py                          # Streamlit 진입점 (프로토타입)
├── docs/
│   ├── concept.md
│   └── architecture.md
├── data/
│   └── patents/
└── requirements.txt
```

**옵션 B+B 호출 흐름:**
```
Django (사용자 요청)
    └─ HTTP → FastAPI /consult
                └─ LangGraph graph.invoke()
                        ├─ node: consulting
                        ├─ node: patent_search  (병렬)
                        ├─ node: claims
                        ├─ node: examiner
                        ├─ node: drawing
                        └─ node: description
                └─ PatentAgentState 반환
    └─ Django → 사용자에게 결과 렌더링
```

---

## 4. 에이전트 파이프라인

```
사용자 입력 (텍스트 / PDF / DOCX / HWP)
        │
        ▼
┌─────────────────────┐
│  Consulting Agent   │  agents/consulting/consultation_agent.py
└────────┬────────────┘
         │ ConsultationResult
         │   - invention_flow   (발명의 전체 흐름)
         │   - problem          (기존 발명의 문제점)
         │   - differentiation  (차별점)
         │   - effect           (효과)
         │
         ├──────────────────────────────────────────────┐
         │                                              │
         ▼                                              ▼
┌─────────────────────┐                   ┌────────────────────────┐
│ Patent Search Agent │                   │    Claims Agent        │
└─────────────────────┘                   └───────────┬────────────┘
  PatentSearchResult                                   │ ClaimsResult
  - similar_patents                                    │   - 독립항 (방법/시스템/기록매체)
  - ipc_codes                                          │   - 종속항
                                                       │
                                                       ▼
                                          ┌────────────────────────┐
                                          │   Examiner Agent       │
                                          └───────────┬────────────┘
                                                       │ ExaminerResult
                                                       │   - 등록가능/불가 의견
                                                       │   - 근거
                                                       │
                              ┌────────────────────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │    Drawing Agent       │  agents/drawing/
                 └───────────┬────────────┘  - drawing_agent.py
                             │ DrawingResult │  - claim_to_flowchart.py
                             │   - mermaid.js 도면 코드
                             │   (흐름도, 시스템구성도)
                             │
         ┌───────────────────┘
         │ (ConsultationResult + DrawingResult)
         ▼
┌─────────────────────────────┐
│     Description Agent       │  agents/description/description_agent.py
└─────────────┬───────────────┘
              │ DescriptionResult
              │   - 배경기술
              │   - 발명의 내용 (과제/해결수단/효과)
              │   - 도면의 간단한 설명
              │   - 발명을 실시하기 위한 구체적인 내용
              ▼
        최종 특허 명세서
```

---

## 5. 각 모듈 인터페이스

> 구현 방식(개별 vs 프레임워크)과 무관하게, 각 에이전트는 아래 input/output 계약을 준수해야 합니다.

### 5-1. Consulting Agent `agents/consulting/consultation_agent.py`

```python
@dataclass
class ConsultationResult:
    invention_flow: str       # 발명의 전체 흐름
    problem: str              # 기존 발명의 문제점
    differentiation: str      # 기존 발명과의 차별점
    effect: str               # 발명의 효과
    raw_conversation: list    # 전체 대화 내역
    user_id: str
    session_id: str

class ConsultingAgent:
    def consult(self, user_input: str) -> ConsultationResult: ...
```

### 5-2. Patent Search Agent `agents/patent_search/patent_search_agent.py`

```python
@dataclass
class PatentSearchResult:
    similar_patents: list     # [{id, title, similarity, summary_problem, summary_solution}]
    ipc_codes: list           # 검색에 사용된 IPC 코드 목록

class PatentSearchAgent:
    def search(self, consultation_result: ConsultationResult) -> PatentSearchResult: ...
```

### 5-3. Claims Agent `agents/claims/claims_agent.py`

```python
@dataclass
class Claim:
    claim_number: int
    claim_type: str           # "method" | "system" | "storage_medium"
    is_independent: bool
    depends_on: int           # 종속항인 경우 인용 항 번호 (독립항은 0)
    content: str

@dataclass
class ClaimsResult:
    claims: list[Claim]

class ClaimsAgent:
    def generate(self, consultation_result: ConsultationResult) -> ClaimsResult: ...
```

### 5-4. Examiner Agent `agents/examiner/examiner_agent.py`

```python
@dataclass
class ExaminerResult:
    is_registerable: bool     # 등록 가능 여부
    opinion: str              # 의견 (등록가능/불가 근거)
    issues: list              # 문제 있는 청구항 목록 [{claim_number, reason}]

class ExaminerAgent:
    def review(self, claims_result: ClaimsResult) -> ExaminerResult: ...
```

### 5-5. Drawing Agent `agents/drawing/drawing_agent.py`

```python
@dataclass
class DrawingResult:
    flowchart_code: str       # mermaid.js 흐름도 코드
    system_diagram_code: str  # mermaid.js 시스템구성도 코드

class DrawingAgent:
    def generate(self, claims_result: ClaimsResult) -> DrawingResult: ...
```

### 5-6. Description Agent `agents/description/description_agent.py`

```python
@dataclass
class DescriptionResult:
    background: str           # 배경기술
    problem_statement: str    # 해결하려는 과제
    solution: str             # 과제의 해결수단
    effect: str               # 발명의 효과
    drawing_description: str  # 도면의 간단한 설명
    detailed_description: str # 발명을 실시하기 위한 구체적인 내용 (실시예)

class DescriptionAgent:
    def generate(
        self,
        consultation_result: ConsultationResult,
        drawing_result: DrawingResult,
    ) -> DescriptionResult: ...
```
