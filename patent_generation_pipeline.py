# patent_generation_pipeline.py
# 발명 설명 output + 청구항 output + 도면 에이전트 + 실시예 에이전트 연결용

import os
import json
from pathlib import Path

from drawing_agent import generate_all_drawings
from embodiment_agent import generate_and_save_embodiment_output


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str | Path, data: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_patent_document_payload(
    invention_output: str | dict,
    claim_output: str | dict,
    embodiment_output: dict,
    drawing_results: list
) -> dict:
    drawings = []

    for result in drawing_results:
        drawings.append({
            "fig_number": getattr(result, "fig_number", ""),
            "diagram_type": getattr(result, "diagram_type", ""),
            "diagram_title": getattr(result, "diagram_title", ""),
            "quality_score": getattr(result, "quality_score", ""),
            "quality_grade": getattr(result, "quality_grade", ""),
            "fig_json_path": getattr(result, "fig_json_path", ""),
            "svg_path": getattr(result, "svg_path", ""),
            "png_path": getattr(result, "png_path", "")
        })

    return {
        "invention_output": invention_output,
        "claim_output": claim_output,
        "drawings": drawings,
        "brief_description_of_drawings": embodiment_output.get(
            "brief_description_of_drawings", []
        ),
        "embodiments": embodiment_output.get("embodiments", [])
    }


def run_full_pipeline(
    invention_text: str,
    app_num: str,
    invention_output: str | dict,
    claim_output: str | dict,
    output_dir: str = "drawing_analysis",
    export_svg: bool = True,
    export_png: bool = True,
    vision_review: bool = False,
    auto_repair: bool = True
) -> dict:
    print("=" * 60)
    print("1. 도면 에이전트 실행")
    print("=" * 60)

    drawing_results = generate_all_drawings(
        invention_text=invention_text,
        app_num=app_num,
        output_dir=output_dir,
        export_svg=export_svg,
        export_png=export_png,
        vision_review=vision_review,
        auto_repair=auto_repair
    )

    print("=" * 60)
    print("2. 도면 설명 + 실시예 에이전트 실행")
    print("=" * 60)

    embodiment_output = generate_and_save_embodiment_output(
        invention_output=invention_output,
        claim_output=claim_output,
        drawing_results=drawing_results,
        output_dir=output_dir,
        app_num=app_num
    )

    final_payload = build_patent_document_payload(
        invention_output=invention_output,
        claim_output=claim_output,
        embodiment_output=embodiment_output,
        drawing_results=drawing_results
    )

    app_dir = Path(output_dir) / app_num
    save_json(app_dir / "final_patent_document_payload.json", final_payload)

    print("=" * 60)
    print("전체 파이프라인 완료")
    print(f"저장 위치: {app_dir}")
    print("=" * 60)

    return final_payload


if __name__ == "__main__":
    sample_invention_text = """
    본 발명은 딥러닝 기반 이미지 분류 시스템에 관한 것이다.
    사용자 단말기(10)는 이미지를 전송한다.
    이미지 분류 시스템(100)은 입력 이미지를 분석한다.
    입력부(110)는 이미지를 입력받는다.
    전처리부(120)는 입력 이미지를 전처리한다.
    CNN 모델부(130)는 전처리된 이미지를 분석한다.
    저장부(140)는 분석 결과를 저장한다.
    출력부(150)는 분류 결과를 출력한다.

    도 1은 이미지 분류 시스템의 전체 구성도이다.
    도 2는 이미지 분류 방법의 처리 흐름도이다.

    부호의 설명
    10: 사용자 단말기
    100: 이미지 분류 시스템
    110: 입력부
    120: 전처리부
    130: CNN 모델부
    140: 저장부
    150: 출력부
    """

    sample_invention_output = {
        "title": "딥러닝 기반 이미지 분류 시스템",
        "technical_problem": "입력 이미지의 분류 정확도를 향상시키는 것",
        "solution": "입력 이미지에 대한 전처리 및 CNN 기반 분석을 수행하는 시스템"
    }

    sample_claim_output = {
        "claim_1": "사용자 단말기로부터 이미지를 수신하는 입력부; 입력 이미지를 전처리하는 전처리부; 전처리된 이미지를 분석하는 CNN 모델부; 분석 결과를 저장하는 저장부; 및 분류 결과를 출력하는 출력부를 포함하는 이미지 분류 시스템."
    }

    run_full_pipeline(
        invention_text=sample_invention_text,
        app_num="TEST-001",
        invention_output=sample_invention_output,
        claim_output=sample_claim_output
    )