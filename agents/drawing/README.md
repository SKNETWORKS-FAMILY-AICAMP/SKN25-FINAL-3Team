# Drawing Agent

특허 명세서를 분석하여 특허청 실무 수준의 SVG 도면을 자동 생성하는 에이전트입니다.

**담당:** bizseohyunkim (김서현)

---

## 지원 도면 유형

| 유형 | 설명 |
|---|---|
| `block_diagram` | 시스템/장치 구성요소 관계 (구성도) |
| `flowchart` | 처리 단계·방법 순서 (흐름도) |

---

## 설치

```bash
pip install openai python-dotenv
```

`.env`:
```
OPENAI_API_KEY=your_api_key_here
```

---

## 실행

```bash
# 테스트 앱
python -m agents.drawing.drawing_test_app

# 직접 실행
python agents/drawing/drawing_agent.py test   # 샘플 테스트
python agents/drawing/drawing_agent.py real   # 실제 특허 1건
```

---

## LangGraph 연동

```python
from agents.drawing.drawing_node import drawing_node

graph.add_node("drawing", drawing_node)
```

- 입력: `state["summary"]["structured_invention"]`
- 출력: `state["drawings"]` (`DrawingAgentOutput.model_dump()`)
- 실패 시 hard fallback 자동 반환

---

## 품질 등급

| 등급 | 점수 |
|---|---|
| A | 90점 이상 |
| B | 75점 이상 |
| C | 60점 이상 |
| D | 60점 미만 |
