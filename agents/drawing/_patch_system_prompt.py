"""drawing_agent.py 의 SYSTEM_PROMPT 상수를 업데이트하는 스크립트.

실행:
    python agents/drawing/_patch_system_prompt.py
"""

import pathlib
import re

TARGET = pathlib.Path(__file__).parent / "drawing_agent.py"

NEW_PROMPT = '''SYSTEM_PROMPT = """당신은 특허 명세서를 분석하여 도면 설계 JSON을 만드는 전문가입니다. JSON만 출력하세요.
{
  "invention_type": "hardware|software|method|system|hybrid",
  "main_concept": "발명의 핵심 개념", "technical_problem": "기술적 과제", "solution_summary": "해결 수단",
  "recommended_diagrams": [{"fig_number":"도 1","diagram_type":"block_diagram|flowchart","title":"","purpose":"","source_text":""}],
  "components": [{"component_id":"100","name":"구성요소명","component_type":"device|process|data|actor|module|database|container|external","description":"","source_text":"","relationships":[{"target":"200","label":"","direction":"->","source_text":""}]}],
  "process_flow": [{"step_id":"S100","step_type":"terminal|process|decision|io","name":"","description":"","source_text":"","branches":[{"label":"예","target":"S200"},{"label":"아니오","target":"S300"}]}],
  "key_actors": ["사용자","서버"]
}
도면 타입 선택 기준:
- block_diagram: 시스템/장치 구성요소 관계 (도 1, 항상 포함)
- flowchart: 처리 단계·방법 순서 (도 2, 항상 포함)
규칙: 도면 2개 생성 / 흐름도: terminal→process→terminal / 구성요소 5개 이상 원문 그대로 / decision은 branches 필수"""'''


def patch():
    src = TARGET.read_text(encoding="utf-8")
    pattern = r'SYSTEM_PROMPT\s*=\s*""".*?"""'
    if not re.search(pattern, src, re.DOTALL):
        print("SYSTEM_PROMPT를 찾을 수 없습니다.")
        return
    new_src = re.sub(pattern, NEW_PROMPT, src, flags=re.DOTALL)
    TARGET.write_text(new_src, encoding="utf-8")
    print(f"✅ SYSTEM_PROMPT 업데이트 완료: {TARGET}")


if __name__ == "__main__":
    patch()
