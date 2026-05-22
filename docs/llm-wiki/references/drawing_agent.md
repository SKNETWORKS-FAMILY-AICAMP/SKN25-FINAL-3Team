# 도면 작성 에이전트 (Drawing Agent) v8

특허 명세서를 분석하여 특허청 실무 수준의 SVG 도면을 자동 생성하는 AI 에이전트입니다.

**담당자:** bizseohyunkim (김서현) — 도면 에이전트 · 발명의 설명 에이전트 · 웹 UI

---

## 지원 도면 유형 (5종)

| 유형 | 렌더러 | 특징 |
|---|---|---|
| `flowchart` | patent_flow_pro | 타원(시작/종료) + 마름모(판단 Yes/No) + 사각형(처리) + 평행사변형(입출력) |
| `block_diagram` | patent_block_pro | 점선 시스템 경계 + 외부 엔티티 + 계층 구조 |
| `sequence` | patent_sequence_pro | 생명선 + 활성화 박스 + 동기/비동기 화살표 |
| `ui_screen` | patent_ui_pro | 디바이스 프레임 + 타입별 UI 요소 |
| `circuit` | patent_circuit_pro | MCU·센서·IoT 하드웨어 전기 연결 회로도 |

> `stateDiagram`은 v8에서 `circuit`으로 대체됨

---

## 발명 특성 기반 자동 도면 선택

텍스트 키워드를 분석하여 적합한 도면 유형을 자동 추가합니다.

| 키워드 | 자동 추가 유형 |
|---|---|
| API, 서버, 통신, 프로토콜 | `sequence` |
| MCU, 센서, 회로, IoT, 임베디드 | `circuit` |
| 화면, UI, 앱, 인터페이스 | `ui_screen` |
| (기본) | `block_diagram`, `flowchart` |

---

## 설치 및 설정

```bash
pip install openai python-dotenv pillow cairosvg
```

`.env` 파일:
```
OPENAI_API_KEY=your_api_key_here
```

---

## 실행

```bash
python drawing_agent.py test          # 샘플 테스트
python drawing_agent.py real          # 실제 특허 1건 (샘플 텍스트 사용)
python drawing_agent.py run 10        # 배치 처리 10건
python drawing_agent.py run 10 --vision        # Vision 검수 포함
python drawing_agent.py analyze <이미지> [특허.txt]  # 이미지 분석
```

| 옵션 | 설명 |
|---|---|
| `--vision` | GPT-4o Vision으로 생성 도면 검수 |
| `--no-svg` / `--no-png` | SVG/PNG 저장 비활성화 |
| `--no-repair` | 자동 품질 보정 끄기 |
| `--repair-rounds N` | 자동 보정 반복 횟수 (기본 1) |

---

## 특허 txt 파일 위치

특허 원문 TXT/PDF는 Git에 포함하지 않습니다. Google Drive 공유 폴더에서 다운로드합니다.

```
공유 드라이브 > final > G06F / G06N / G06Q / G06V
공유 드라이브 > final > extracted_texts
```

Drive 목록은 `data/manifests/`에서 관리합니다.

---

## LangGraph 연동 (drawing_node.py)

```python
from agents.drawing.drawing_node import drawing_node

# LangGraph 노드로 사용
graph.add_node("drawing", drawing_node)
graph.add_edge("drawing", "specification")
```

- 입력: `state["consultation"]` 또는 `state["summary"]["structured_invention"]`
- 출력: `state["drawings"]` (DrawingAgentOutput.model_dump())
- 실패 시 hard fallback 자동 반환 (파이프라인 중단 없음)

---

## 출력 파일 구조

```
drawing_analysis/{출원번호}/       ← .gitignore 처리됨
├── local_extraction.json
├── patent_analysis.json
├── figures.json
├── {번호}_fig_1.svg/.png
├── {번호}_fig_1_layout.json
├── {번호}_fig_1_validation.json
└── report.md
```

---

## 품질 등급

| 등급 | 점수 | 기준 |
|---|---|---|
| A | 90+ | 도면부호 완비, 구성요소 충분, 렌더러 정상 |
| B | 75+ | 통과 기준 |
| C | 60+ | 검토 필요 |
| D | 60미만 | 자동 보정 대상 |

---

## 외부 호출

```python
from agents.drawing.drawing_agent import generate_all_drawings

results = generate_all_drawings(
    invention_text="특허 명세서 전문...",
    app_num="출원번호",
    export_svg=True,
)
for r in results:
    print(r.svg_path, r.quality_score)
```

---

## 파이프라인 위치

```
상담 에이전트 → 선행기술조사 → 청구항 → 도면 에이전트 ← 이 파일
                                               ↓
                                      발명의 설명 에이전트 → 최종 명세서
```

---

## 버전 이력

| 버전 | 변경 내용 |
|---|---|
| v8 | 회로도(circuit) 렌더러 추가, 발명 특성 기반 자동 도면 선택, LangGraph drawing_node 연동, DrawingAgentOutput Pydantic schema 적용 |
| v7.2 | 코드 리팩토링: 1,567줄 → 784줄 (50% 감소) |
| v7.1 | Streamlit 웹 UI 페이지 추가 |
| v7 | 흐름도 타원/마름모, 시퀀스 활성화 박스, 상태도 둥근 사각형, UI 디바이스 프레임 |
| v6 | 시퀀스/상태도/UI 렌더러 추가 |
| v5 | Mermaid 제거, SVG 직접 렌더링으로 전환 |
