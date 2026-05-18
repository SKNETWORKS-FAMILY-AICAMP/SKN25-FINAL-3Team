# embodiment_agent.py
# 도면의 간단한 설명 + 도면별 실시예 생성 에이전트

import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_TEXT = "gpt-4o-mini"


def safe_json_loads(raw: str) -> dict:
    raw = re.sub(r"```json\s*|\s*```", "", str(raw).strip()).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())

    raise ValueError("JSON 파싱 실패")


def save_json(path: str | Path, data: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


SYSTEM_PROMPT = """
당신은 특허 명세서 작성 전문가입니다.

입력으로 제공되는 정보는 다음과 같습니다.
1. 발명 설명 에이전트 출력
2. 청구항 에이전트 출력
3. 도면 에이전트 출력 fig_json 목록

당신의 역할은 다음 두 가지입니다.

1. 도면의 간단한 설명 작성
2. 도면별 실시예 작성

반드시 JSON만 출력하세요.

출력 형식:
{
  "brief_description_of_drawings": [
    {
      "fig_number": "도 1",
      "description": "도 1은 ... 도시한 도면이다."
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

작성 규칙:
- 도면 하나당 brief_description 1개, embodiment 1개를 작성하세요.
- 도면 JSON의 elements, relations, title, diagram_type을 근거로 작성하세요.
- 청구항에 없는 핵심 구성을 새로 만들지 마세요.
- 발명 설명에 없는 기술 효과를 과장하지 마세요.
- 문체는 특허 명세서 문체로 작성하세요.
- 실시예는 "본 발명의 일 실시예에 따르면"으로 자연스럽게 시작하세요.
- 각 실시예는 도면에 포함된 구성요소와 동작 관계를 설명해야 합니다.
- 도면부호 또는 단계부호가 있으면 문장에 자연스럽게 포함하세요.
- 너무 짧게 쓰지 말고, 도면당 2~5문단 정도로 작성하세요.
"""


def generate_drawing_description_and_embodiments(
    invention_output: str | dict,
    claim_output: str | dict,
    figures: list
) -> dict:
    if isinstance(invention_output, dict):
        invention_output = json.dumps(invention_output, ensure_ascii=False, indent=2)

    if isinstance(claim_output, dict):
        claim_output = json.dumps(claim_output, ensure_ascii=False, indent=2)

    prompt = f"""
[발명 설명 에이전트 출력]
{invention_output}

[청구항 에이전트 출력]
{claim_output}

[도면 에이전트 출력 fig_json 목록]
{json.dumps(figures, ensure_ascii=False, indent=2)}

위 정보를 기반으로 도면의 간단한 설명과 도면별 실시예를 작성하세요.
"""

    response = client.chat.completions.create(
        model=MODEL_TEXT,
        temperature=0.2,
        max_tokens=6000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    return safe_json_loads(response.choices[0].message.content)


def generate_and_save_embodiment_output(
    invention_output: str | dict,
    claim_output: str | dict,
    drawing_results: list,
    output_dir: str = "drawing_analysis",
    app_num: str = "UNKNOWN"
) -> dict:
    figures = []

    for result in drawing_results:
        fig_json_path = getattr(result, "fig_json_path", "")

        if not fig_json_path or not os.path.exists(fig_json_path):
            continue

        with open(fig_json_path, "r", encoding="utf-8") as f:
            fig_json = json.load(f)

        figures.append({
            "fig_number": getattr(result, "fig_number", ""),
            "title": getattr(result, "diagram_title", ""),
            "diagram_type": getattr(result, "diagram_type", ""),
            "fig_json": fig_json
        })

    output = generate_drawing_description_and_embodiments(
        invention_output=invention_output,
        claim_output=claim_output,
        figures=figures
    )

    app_dir = Path(output_dir) / app_num
    save_json(app_dir / "embodiment_output.json", output)

    return output