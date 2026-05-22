"""명세서 파일 기반 스토리지 모듈.

생성된 특허 명세서 결과를 Markdown(.md) 파일 형태로 포맷팅하여 로컬 파일 시스템에 저장하고,
필요 시 마크다운 파일을 로드하여 조회할 수 있는 기능을 제공합니다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

def convert_to_markdown_format(
    invention_title: str,
    spec_dict: dict[str, Any],
) -> str:
    """명세서 dict를 한국 특허 명세서 형식의 Markdown 문자열로 변환합니다.

    spec_dict는 아래 두 형태를 모두 허용합니다:
    1) SpecificationAgentOutput 전체 dict (또는 Pydantic 객체)
    2) specification 섹션 dict

    내부에서 다음처럼 처리하여 유연성을 높입니다:
    spec = spec_dict.get("specification", spec_dict)
    """
    # Pydantic 모델인 경우 dict로 변환
    if hasattr(spec_dict, "model_dump"):
        spec_dict = spec_dict.model_dump()
    elif hasattr(spec_dict, "dict"):
        spec_dict = spec_dict.dict()

    if not isinstance(spec_dict, dict):
        raise TypeError("spec_dict는 dict 형태 또는 Pydantic 객체여야 합니다.")

    # 1) 'specification' 키 아래에 필드가 있는지, 아니면 루트에 있는지 확인
    spec = spec_dict.get("specification", spec_dict)
    if not isinstance(spec, dict):
        spec = spec_dict

    # 각 섹션 값 추출 (기본값 "")
    technical_field = spec.get("technical_field") or spec_dict.get("technical_field") or ""
    background_art = spec.get("background_art") or spec_dict.get("background_art") or ""
    problem_to_solve = spec.get("problem_to_solve") or spec_dict.get("problem_to_solve") or ""
    means_for_solving = spec.get("means_for_solving") or spec_dict.get("means_for_solving") or ""
    effects = spec.get("effects") or spec_dict.get("effects") or ""
    brief_description_of_drawings = spec.get("brief_description_of_drawings") or spec_dict.get("brief_description_of_drawings") or ""
    detailed_description = spec.get("detailed_description") or spec_dict.get("detailed_description") or ""

    # 양끝 공백 제거
    invention_title = str(invention_title).strip()
    technical_field = str(technical_field).strip()
    background_art = str(background_art).strip()
    problem_to_solve = str(problem_to_solve).strip()
    means_for_solving = str(means_for_solving).strip()
    effects = str(effects).strip()
    brief_description_of_drawings = str(brief_description_of_drawings).strip()
    detailed_description = str(detailed_description).strip()

    # Markdown 포맷 문자열 템플릿 생성
    markdown_content = f"""# [특허 명세서] 발명의 설명

## 발명의 명칭

{invention_title}

## 기술분야

{technical_field}

## 배경기술

{background_art}

## 해결하고자 하는 과제

{problem_to_solve}

## 과제의 해결수단

{means_for_solving}

## 발명의 효과

{effects}

## 도면의 간단한 설명

{brief_description_of_drawings}

## 발명을 실시하기 위한 구체적인 내용

{detailed_description}"""

    return markdown_content


def save_specification(
    user_id: str,
    consultation_idx: int,
    spec_dict: dict[str, Any],
    invention_title: str = "",
    save_json: bool = False,
    base_dir: str = "data/specifications",
) -> dict[str, str]:
    """data/specifications/{user_id}/{consultation_idx}/specification.md를 저장합니다.
    save_json=True이면 같은 디렉토리에 specification.json도 저장합니다.

    현재 MVP에서는 같은 user_id/consultation_idx에 대해 최신본을 덮어쓰기합니다.

    반환값:
    {
        "markdown_path": "...",
        "json_path": "..."  # save_json=True일 때만 포함
    }
    """
    # 1. 경로 정의
    dir_path = Path(base_dir) / str(user_id) / str(consultation_idx)
    dir_path.mkdir(parents=True, exist_ok=True)

    md_path = dir_path / "specification.md"
    
    # 2. 마크다운 변환 및 저장
    markdown_content = convert_to_markdown_format(invention_title, spec_dict)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    results = {
        "markdown_path": str(md_path)
    }

    # 3. JSON 저장 (선택 옵션)
    if save_json:
        json_path = dir_path / "specification.json"
        
        # Pydantic 모델인 경우 안전하게 직렬화 가능한 dict로 변환
        serializable_spec = spec_dict
        if hasattr(spec_dict, "model_dump"):
            serializable_spec = spec_dict.model_dump()
        elif hasattr(spec_dict, "dict"):
            serializable_spec = spec_dict.dict()
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(serializable_spec, f, ensure_ascii=False, indent=2)
        
        results["json_path"] = str(json_path)

    return results


def get_specification_markdown_path(
    user_id: str,
    consultation_idx: int,
    base_dir: str = "data/specifications",
) -> str:
    """해당 상담 회차의 specification.md 경로를 반환합니다."""
    path = Path(base_dir) / str(user_id) / str(consultation_idx) / "specification.md"
    return str(path)


def load_specification_markdown(
    user_id: str,
    consultation_idx: int,
    base_dir: str = "data/specifications",
) -> str:
    """해당 상담 회차의 specification.md 내용을 읽어 반환합니다."""
    path = Path(get_specification_markdown_path(user_id, consultation_idx, base_dir))
    if not path.exists():
        raise FileNotFoundError(f"저장된 명세서 파일을 찾을 수 없습니다. (경로: {path})")
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
