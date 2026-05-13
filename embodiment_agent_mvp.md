# Embodiment Agent — MVP 문서

> 특허 명세서 자동 작성 파이프라인 중 **도면의 간단한 설명** 및 **도면별 실시예**를 생성하는 에이전트

---

## 1. 개요

`embodiment_agent.py`는 특허 명세서 작성 파이프라인의 후단 에이전트입니다.  
앞선 세 에이전트(발명 설명 · 청구항 · 도면)의 출력물을 입력받아, 특허 명세서에 필수적인 두 섹션을 자동으로 생성합니다.

| 생성 섹션 | 설명 |
|---|---|
| **도면의 간단한 설명** | 각 도면(도 1, 도 2 …)이 무엇을 나타내는지 한 문장으로 기술 |
| **도면별 실시예** | 각 도면을 참조하여 구성요소·동작 관계를 2~5문단으로 상세 기술 |

---

## 2. 에이전트 아키텍처

```
┌─────────────────────┐
│   발명 설명 에이전트  │  (invention_output)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   청구항 에이전트    │  (claim_output)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   도면 에이전트      │  (drawing_results → fig_json 파일들)
└──────────┬──────────┘
           │
┌──────────▼──────────────────────────────────────┐
│            Embodiment Agent                      │
│                                                  │
│  1. fig_json 파일 수집 (drawing_results 순회)    │
│  2. LLM 프롬프트 조합                           │
│  3. GPT-4o-mini 호출                            │
│  4. JSON 파싱 & 저장                            │
└──────────┬──────────────────────────────────────┘
           │
   embodiment_output.json
```

---

## 3. 입력 / 출력 스펙

### 3-1. 입력

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `invention_output` | `str \| dict` | 발명 설명 에이전트 출력 (JSON 또는 문자열) |
| `claim_output` | `str \| dict` | 청구항 에이전트 출력 |
| `drawing_results` | `list` | 도면 에이전트 결과 객체 리스트. 각 객체는 `fig_json_path`, `fig_number`, `diagram_title`, `diagram_type` 속성을 가짐 |
| `output_dir` | `str` | 결과 저장 루트 디렉토리 (기본값: `"drawing_analysis"`) |
| `app_num` | `str` | 출원번호 (서브디렉토리명으로 사용, 기본값: `"UNKNOWN"`) |

### 3-2. 출력 JSON 구조

```json
{
  "brief_description_of_drawings": [
    {
      "fig_number": "도 1",
      "description": "도 1은 본 발명의 일 실시예에 따른 시스템 구성을 도시한 도면이다."
    }
  ],
  "embodiments": [
    {
      "fig_number": "도 1",
      "title": "도 1에 따른 실시예",
      "content": "도 1을 참조하면, ..."
    }
  ]
}
```

파일 저장 경로: `{output_dir}/{app_num}/embodiment_output.json`

---

## 4. 핵심 함수 설명

### `generate_drawing_description_and_embodiments()`

LLM을 직접 호출하는 **핵심 생성 함수**입니다.

```python
def generate_drawing_description_and_embodiments(
    invention_output: str | dict,
    claim_output: str | dict,
    figures: list
) -> dict
```

- `invention_output`, `claim_output`이 `dict`이면 자동으로 JSON 문자열 변환
- 시스템 프롬프트 + 유저 프롬프트를 조합하여 `gpt-4o-mini` 호출
- `temperature=0.2` → 일관성 있는 특허 문체 유지
- `max_tokens=6000` → 다수 도면 처리 시 충분한 출력 확보
- 반환값: 파싱된 `dict` (JSON)

---

### `generate_and_save_embodiment_output()`

파이프라인 진입점 역할의 **오케스트레이터 함수**입니다.

```python
def generate_and_save_embodiment_output(
    invention_output, claim_output,
    drawing_results, output_dir, app_num
) -> dict
```

처리 흐름:

1. `drawing_results` 순회 → `fig_json_path` 존재 확인 → JSON 파일 로드
2. 도면별 메타정보(`fig_number`, `title`, `diagram_type`, `fig_json`) 취합
3. `generate_drawing_description_and_embodiments()` 호출
4. `{output_dir}/{app_num}/embodiment_output.json`에 저장

---

### `safe_json_loads()`

LLM 응답의 **방어적 JSON 파싱** 유틸리티입니다.

```python
def safe_json_loads(raw: str) -> dict
```

| 단계 | 처리 내용 |
|---|---|
| 1 | ` ```json ``` ` 마크다운 펜스 제거 |
| 2 | `json.loads()` 직접 시도 |
| 3 | 실패 시 정규식으로 `{...}` 블록 추출 후 재시도 |
| 4 | 모두 실패 시 `ValueError` 발생 |

---

## 5. 시스템 프롬프트 설계 원칙

```
역할: 특허 명세서 작성 전문가
출력 제약: 반드시 JSON만 출력 (마크다운 불가)
```

| 규칙 | 목적 |
|---|---|
| 도면당 brief_description 1개 + embodiment 1개 | 명세서 구조 일관성 |
| 청구항에 없는 구성 추가 금지 | 청구 범위 보호 |
| 발명 설명에 없는 효과 과장 금지 | 허위 기재 방지 |
| 도면부호·단계부호 자연스럽게 포함 | 특허 문체 준수 |
| 2~5문단 분량 | 명세서 완성도 확보 |
| `"본 발명의 일 실시예에 따르면"` 으로 시작 | 실시예 표준 문체 |

---

## 6. 파일 구조

```
embodiment_agent.py          # 본 에이전트 단일 파일
drawing_analysis/
└── {app_num}/
    └── embodiment_output.json   # 생성 결과
```

도면 에이전트가 생성한 fig_json 파일들은 `drawing_results` 객체의  
`fig_json_path` 속성으로 경로를 참조합니다.

---

## 7. 의존성

```
openai>=1.0.0
python-dotenv
```

환경변수 `.env`:
```
OPENAI_API_KEY=sk-...
```

사용 모델: `gpt-4o-mini` (`MODEL_TEXT` 상수로 관리)

---

## 8. 사용 예시

```python
from embodiment_agent import generate_and_save_embodiment_output

# 앞선 에이전트 출력물 준비
invention_output = {...}   # 발명 설명 에이전트 결과 dict
claim_output = {...}       # 청구항 에이전트 결과 dict
drawing_results = [...]    # 도면 에이전트 결과 객체 리스트

# 실행
result = generate_and_save_embodiment_output(
    invention_output=invention_output,
    claim_output=claim_output,
    drawing_results=drawing_results,
    output_dir="drawing_analysis",
    app_num="10-2024-0012345"
)

# 결과 확인
print(result["brief_description_of_drawings"])
print(result["embodiments"])
```

---

## 9. MVP 한계 및 향후 개선 방향

| 항목 | 현재 MVP | 향후 개선 |
|---|---|---|
| 모델 | `gpt-4o-mini` 고정 | 모델 파라미터화, Claude 전환 검토 |
| 오류 처리 | `ValueError` 발생 | 재시도 로직(retry) 추가 |
| 도면 누락 | 경로 없으면 skip | 누락 도면 경고 로그 출력 |
| 토큰 제한 | `max_tokens=6000` 고정 | 도면 수에 따라 동적 조정 |
| 검증 | 없음 | 생성된 JSON 스키마 검증 추가 |
| 병렬 처리 | 단일 LLM 호출 | 도면 수 많을 시 배치 분할 호출 |
