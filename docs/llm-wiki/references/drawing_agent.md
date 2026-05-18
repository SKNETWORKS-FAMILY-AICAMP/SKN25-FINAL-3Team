# 도면 작성 에이전트 (Drawing Agent) v7.1

특허 명세서를 분석하여 특허청 실무 수준의 도면을 자동 생성하는 AI 에이전트입니다.

## 담당자

- **bizseohyunkim** (김서현) — 도면 에이전트, 발명의 설명 에이전트, 웹 UI

---

## 주요 기능

| 기능 | 설명 |
|---|---|
| 특허 txt 파싱 | 청구범위, 발명의 설명, 도면 목록, 부호 설명 자동 추출 |
| LLM 분석 | GPT-4o-mini 기반 구성요소 및 처리 흐름 분석 |
| SVG 직접 렌더링 | 좌표 기반 특허청 스타일 도면 생성 |
| PNG 변환 | SVG → PNG 자동 변환 |
| 품질 검증 | 도면부호, 구성요소 수, 레이아웃 기반 자동 점수 산출 |
| 자동 수정 | 품질 기준 미달 시 LLM 기반 자동 보정 |
| Vision 검수 | GPT-4o Vision으로 생성된 도면 품질 검수 (선택) |

---

## 지원 도면 유형

| 유형 | 렌더러 | 특징 |
|---|---|---|
| `flowchart` | patent_flow_pro | 타원(시작/종료) + 마름모(판단/Yes/No) + 사각형(처리) + 평행사변형(입출력) |
| `block_diagram` | patent_block_pro | 점선 시스템 경계 + 외부 엔티티 + 계층 구조 |
| `sequence` | patent_sequence_pro | 생명선 + 활성화 박스 + 동기/비동기 화살표 |
| `stateDiagram` | patent_state_pro | 둥근 사각형 상태 노드 + 초기/종료 마커 + 곡선 전이 |
| `ui_screen` | patent_ui_pro | 디바이스 프레임 + 타입별 UI 요소 |

---

## 설치

```bash
pip install openai python-dotenv pillow cairosvg
```

`.env` 파일 설정:
```
OPENAI_API_KEY=your_api_key_here
```

---

## Streamlit 웹 UI

`patentai_ui.py` 메인 네비게이션에 **도면 에이전트** 메뉴가 추가되었습니다.

```bash
streamlit run patentai_ui.py
```

브라우저에서 상단 메뉴 **도면 에이전트** 클릭 또는 `/도면_에이전트` 직접 접근.

| 기능 | 설명 |
|---|---|
| 발명 텍스트 입력 | 명세서 텍스트 붙여넣기 |
| 출원번호 설정 | 결과 저장 폴더명으로 사용 |
| SVG 인라인 표시 | 생성된 도면 즉시 확인 |
| SVG / PNG 다운로드 | 버튼 클릭으로 파일 저장 |
| 자동 품질 보정 | 품질 기준 미달 시 자동 재생성 |

관련 파일:
- `pages/2_도면_에이전트.py` — Streamlit 페이지
- `patentai_ui.py` — 네비게이션 링크

---

## 실행 방법

### 샘플 테스트
```bash
python drawing_agent.py test
```

### 실제 특허 파일 1건 테스트
```bash
python drawing_agent.py real
```

### 배치 처리 (N건)
```bash
python drawing_agent.py run 10
```

### 옵션

| 옵션 | 설명 |
|---|---|
| `--vision` | 생성된 PNG를 GPT-4o Vision으로 검수 |
| `--no-svg` | SVG 저장 끄기 |
| `--no-png` | PNG 변환 끄기 |
| `--no-repair` | 자동 품질 보정 끄기 |
| `--repair-rounds N` | 자동 보정 반복 횟수 (기본 1) |

```bash
# 예시
python drawing_agent.py run 10 --vision
python drawing_agent.py run 10 --no-png
```

---

## 특허 txt 파일 위치

```
SKN25-FINAL-3Team/
├── G06F/    ← 특허 txt 파일
├── G06N/
├── G06Q/
└── G06V/
```

---

## 출력 파일 구조

```
drawing_analysis/
└── {출원번호}/
    ├── local_extraction.json       # 정규식 기반 도면/부호 추출
    ├── patent_analysis.json        # LLM 기반 발명 분석
    ├── figures.json                # 생성 대상 도면 목록
    ├── {번호}_fig_1.json           # 도면 설계 JSON
    ├── {번호}_fig_1.svg            # 특허청 스타일 SVG
    ├── {번호}_fig_1.png            # PNG 변환본
    ├── {번호}_fig_1_layout.json    # 레이아웃 메타데이터
    ├── {번호}_fig_1_validation.json # 품질 검증 결과
    └── report.md                   # 생성 리포트
```

---

## 품질 기준

| 등급 | 점수 | 기준 |
|---|---|---|
| A | 90점 이상 | 도면부호 완비, 구성요소 충분, 렌더러 정상 |
| B | 75점 이상 | 통과 기준 |
| C | 60점 이상 | 검토 필요 |
| D | 60점 미만 | 자동 보정 대상 |

---

## 파이프라인 연동

다른 에이전트와의 연동 구조:

```
상담 에이전트
    ↓ 상담 노트
선행기술조사 에이전트
    ↓ 분석 결과
명세서 작성 에이전트 (청구항 sLLM)
    ↓ 전체 청구항
도면 에이전트  ←── 이 파일
    ↓ SVG/PNG
발명의 설명 에이전트
    ↓
최종 특허 명세서
```

### 외부 호출 예시

```python
from drawing_agent import generate_all_drawings

results = generate_all_drawings(
    invention_text="특허 명세서 전문...",
    app_num="출원번호",
    output_dir="drawing_analysis",
    export_svg=True,
    export_png=True,
)

for r in results:
    print(r.svg_path)   # SVG 경로
    print(r.png_path)   # PNG 경로
    print(r.quality_score)  # 품질 점수
```

---

## 버전 이력

| 버전 | 변경 내용 |
|---|---|
| v7.1 | Streamlit 웹 UI 페이지 추가, patentai_ui.py 네비게이션 연동 |
| v7 | 흐름도 타원/마름모 추가, 시퀀스 활성화 박스, 상태도 둥근 사각형, UI 디바이스 프레임 |
| v6 | 시퀀스/상태도/UI 렌더러 추가 |
| v5 | Mermaid 제거, SVG 직접 렌더링으로 전환 |
