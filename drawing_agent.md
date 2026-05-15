# 도면 작성 에이전트 (Drawing Agent) v7.2

특허 명세서를 분석하여 특허청 실무 수준의 SVG 도면을 자동 생성하는 AI 에이전트입니다.

**담당자:** bizseohyunkim (김서현) — 도면 에이전트 · 발명의 설명 에이전트 · 웹 UI

---

## 지원 도면 유형

| 유형 | 렌더러 | 특징 |
|---|---|---|
| `flowchart` | patent_flow_pro | 타원(시작/종료) + 마름모(판단 Yes/No) + 사각형(처리) + 평행사변형(입출력) |
| `block_diagram` | patent_block_pro | 점선 시스템 경계 + 외부 엔티티 + 계층 구조 |
| `sequence` | patent_sequence_pro | 생명선 + 활성화 박스 + 동기/비동기 화살표 |
| `stateDiagram` | patent_state_pro | 둥근 사각형 + 초기/종료 마커 + 곡선 전이 |
| `ui_screen` | patent_ui_pro | 디바이스 프레임 + 타입별 UI 요소 |

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
python drawing_agent.py real          # 실제 특허 1건
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

```
SKN25-FINAL-3Team/
├── G06F/ ├── G06N/ ├── G06Q/ └── G06V/  ← 특허 txt 파일
```

---

## 출력 파일 구조

```
drawing_analysis/{출원번호}/
├── local_extraction.json     # 정규식 기반 도면/부호 추출
├── patent_analysis.json      # LLM 기반 발명 분석
├── figures.json              # 생성 대상 도면 목록
├── {번호}_fig_1.svg/.png     # 특허청 스타일 도면
├── {번호}_fig_1_layout.json  # 레이아웃 메타데이터
├── {번호}_fig_1_validation.json  # 품질 검증 결과
└── report.md                 # 생성 리포트
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
from drawing_agent import generate_all_drawings

results = generate_all_drawings(
    invention_text="특허 명세서 전문...",
    app_num="출원번호",
    export_svg=True, export_png=True,
)
for r in results:
    print(r.svg_path, r.quality_score)
```

---

## 파이프라인 위치

```
상담 에이전트 → 선행기술조사 → 명세서 작성 → 도면 에이전트 ← 이 파일
                                                      ↓
                                             발명의 설명 에이전트 → 최종 명세서
```

---

## 버전 이력

| 버전 | 변경 내용 |
|---|---|
| v7.2 | 코드 리팩토링: 1,567줄 → 784줄 (50% 감소), 동일 SVG 출력 유지 |
| v7.1 | Streamlit 웹 UI 페이지 추가, patentai_ui.py 네비게이션 연동 |
| v7 | 흐름도 타원/마름모, 시퀀스 활성화 박스, 상태도 둥근 사각형, UI 디바이스 프레임 |
| v6 | 시퀀스/상태도/UI 렌더러 추가 |
| v5 | Mermaid 제거, SVG 직접 렌더링으로 전환 |
