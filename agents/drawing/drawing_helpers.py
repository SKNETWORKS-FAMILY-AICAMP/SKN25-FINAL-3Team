"""도면 에이전트 내부에서 사용하는 헬퍼 유틸리티.

JSON 파싱, SVG 유틸, 품질 설정, Config 등을 담당한다.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 1. Config
# ---------------------------------------------------------------------------

@dataclass
class DrawingAgentConfig:
    model_text: str = ""
    model_vision: str = ""
    quality_pass_score: int = 75
    auto_repair_rounds: int = 1
    max_block_elements: int = 14
    max_flow_steps: int = 14

    def __post_init__(self):
        if not self.model_text:
            self.model_text = os.getenv("OPENAI_DRAWING_MODEL", "gpt-4o-mini")
        if not self.model_vision:
            self.model_vision = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")


# ---------------------------------------------------------------------------
# 2. JSON 파싱 유틸리티
# ---------------------------------------------------------------------------

def safe_parse_json(text: str) -> dict | None:
    """LLM 응답에서 JSON 객체를 안전하게 추출한다."""
    text = re.sub(r"```json\s*|\s*```", "", str(text).strip()).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return None


# ---------------------------------------------------------------------------
# 3. 텍스트 유틸리티
# ---------------------------------------------------------------------------

def normalize_space(text: str) -> str:
    """연속 공백을 단일 공백으로 정규화한다."""
    return re.sub(r"\s+", " ", str(text or "")).strip()


def escape_xml(s: str) -> str:
    """SVG/XML 특수문자를 이스케이프한다."""
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def truncate(text: str, n: int = 20) -> str:
    """텍스트를 n자로 잘라낸다."""
    text = normalize_space(text)
    return text if len(text) <= n else text[:n - 1] + "…"


# ---------------------------------------------------------------------------
# 4. 도면 유형 판별
# ---------------------------------------------------------------------------

def is_decision_step(name: str, step_type: str = "") -> bool:
    """흐름도 단계가 판단(decision)인지 확인한다."""
    if step_type == "decision":
        return True
    return any(k in name for k in ["판단", "확인", "검사", "여부", "인지", "결정", "선택", "검증", "체크", "비교"])


def is_terminal_step(name: str, step_type: str = "", idx: int = -1, total: int = 0) -> bool:
    """흐름도 단계가 시작/종료(terminal)인지 확인한다."""
    if step_type == "terminal":
        return True
    if idx == 0 and any(k in name for k in ["시작", "START", "start", "begin", "Begin"]):
        return True
    if idx == total - 1 and any(k in name for k in ["종료", "END", "end", "완료", "finish", "Finish"]):
        return True
    return False


# ---------------------------------------------------------------------------
# 5. 품질 등급 계산
# ---------------------------------------------------------------------------

def get_quality_grade(score: int) -> str:
    """점수를 A/B/C/D 등급으로 변환한다."""
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    return "D"
