# drawing_agent.py - 특허청 스타일 SVG 직접 렌더링 Agent v5
# 목표:
# 1. 특허 txt 파싱
# 2. 특허 구성요소/단계 분석 JSON 생성
# 3. Mermaid 자동배치 대신 좌표 기반 SVG 직접 생성
# 4. 특허청 실무형 블록도/흐름도 레이아웃 생성
# 5. SVG/PNG/JSON/report 저장
#
# 실행:
#   python drawing_agent.py test
#   python drawing_agent.py real
#   python drawing_agent.py run 10

import os
import io
import glob
import json
import re
import math
import shutil
import datetime
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Tuple
from dotenv import load_dotenv
from openai import OpenAI

try:
    import base64
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[경고] Pillow 미설치: pip install Pillow")

try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("[경고] pdf2image 미설치: pip install pdf2image")

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except Exception:
    CAIROSVG_AVAILABLE = False


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_TEXT = "gpt-4o-mini"
MODEL_VISION = "gpt-4o"

PATENT_DIRS = ["G06F", "G06N", "G06Q", "G06V"]
QUALITY_PASS_SCORE = 75
AUTO_REPAIR_DEFAULT_ROUNDS = 1
DEFAULT_STYLE_TEMPLATE = "patent_office"

MAX_BLOCK_ELEMENTS = 14
MAX_FLOW_STEPS = 12

FONT_FAMILY = "NanumGothic, Noto Sans CJK KR, Noto Sans KR, Malgun Gothic, Arial, sans-serif"


@dataclass
class DrawingResult:
    app_num: str
    fig_number: str
    diagram_type: str
    diagram_title: str
    quality_score: int
    quality_grade: str
    fig_json_path: str
    svg_path: str
    png_path: str = ""
    layout_path: str = ""
    validation_path: str = ""
    vision_path: str = ""
    style_template: str = DEFAULT_STYLE_TEMPLATE
    auto_repaired: bool = False
    repair_rounds: int = 0


# =========================================================
# 공통 유틸
# =========================================================

def safe_json_loads(raw: str) -> dict:
    raw = re.sub(r"```json\s*|\s*```", "", str(raw).strip()).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
    raise ValueError("JSON 파싱 실패")


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def xml_escape(s: str) -> str:
    s = str(s or "")
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def truncate(text: str, n: int = 18) -> str:
    text = normalize_space(text)
    return text if len(text) <= n else text[: n - 1] + "…"


# =========================================================
# 특허 텍스트 파싱
# =========================================================

def extract_section(text: str, start_keywords: list, end_keywords: list) -> str:
    start = -1
    for kw in start_keywords:
        idx = text.find(kw)
        if idx != -1:
            start = idx
            break
    if start == -1:
        return ""

    end_candidates = []
    for kw in end_keywords:
        idx = text.find(kw, start + 1)
        if idx != -1:
            end_candidates.append(idx)

    end = min(end_candidates) if end_candidates else start + 6000
    return text[start:end].strip()


def parse_patent_txt(txt_file: str) -> dict:
    with open(txt_file, "r", encoding="utf-8-sig") as f:
        text = f.read()

    app_num = os.path.basename(txt_file).replace(".txt", "")

    claims = extract_section(
        text,
        ["청구범위"],
        ["발명의 설명", "요약", "도면의 간단한 설명"]
    )

    detail = extract_section(
        text,
        ["발명의 설명", "발명의 상세한 설명", "상세한 설명"],
        ["청구범위"]
    )

    figure_desc = extract_section(
        text,
        ["도면의 간단한 설명"],
        ["발명을 실시하기 위한 구체적인 내용", "발명의 효과", "부호의 설명"]
    )

    reference_desc = extract_section(
        text,
        ["부호의 설명"],
        ["청구범위", "요약", "산업상 이용가능성"]
    )

    full = f"""
[청구범위]
{claims}

[도면의 간단한 설명]
{figure_desc}

[부호의 설명]
{reference_desc}

[발명의 상세한 설명]
{detail}
""".strip()

    return {
        "app_num": app_num,
        "claims": claims,
        "detail": detail,
        "figure_desc": figure_desc,
        "reference_desc": reference_desc,
        "full": full
    }


# =========================================================
# 도면 목록 / 부호 설명 추출
# =========================================================

def classify_diagram_type(title: str) -> str:
    title = title or ""
    if any(k in title for k in ["순서도", "흐름도", "플로우", "과정", "절차", "방법", "단계"]):
        return "flowchart"
    if any(k in title for k in ["구성도", "시스템", "장치", "블록도", "구조도", "모듈"]):
        return "block_diagram"
    if any(k in title for k in ["화면", "UI", "인터페이스", "표시"]):
        return "ui_screen"
    if any(k in title for k in ["시퀀스", "상호작용", "통신"]):
        return "sequence"
    if any(k in title for k in ["상태"]):
        return "stateDiagram"
    return "concept_diagram"


def extract_figure_list(text: str) -> list:
    figures = []
    patterns = [
        r"도\s*(\d+[A-Za-z]?)\s*(?:은|는)\s*([^\n\.]+)",
        r"\[도\s*(\d+[A-Za-z]?)\]\s*([^\n]+)",
        r"도\s*(\d+[A-Za-z]?)\s*[:：]\s*([^\n]+)"
    ]
    seen = set()

    for pattern in patterns:
        for m in re.finditer(pattern, text):
            fig_no = f"도 {m.group(1)}"
            title = normalize_space(m.group(2))
            if fig_no in seen:
                continue
            seen.add(fig_no)
            figures.append({
                "fig_number": fig_no,
                "title": title,
                "diagram_type": classify_diagram_type(title),
                "purpose": title,
                "source_text": m.group(0).strip()
            })

    def fig_sort_key(x):
        nums = re.findall(r"\d+", x["fig_number"])
        return int(nums[0]) if nums else 9999

    figures.sort(key=fig_sort_key)
    return figures


def extract_reference_numbers(text: str) -> list:
    refs = []
    patterns = [
        r"(\d{2,5})\s*[:：]\s*([^\n,;]+)",
        r"(\d{2,5})\s*[\.]\s*([^\n,;]+)",
        r"(\d{2,5})\s*[-–]\s*([^\n,;]+)",
        r"([가-힣A-Za-z0-9\s]+)\((\d{2,5})\)"
    ]
    seen = set()

    for pattern in patterns:
        for m in re.finditer(pattern, text):
            if len(m.groups()) >= 2 and m.group(1).isdigit():
                ref_no = m.group(1).strip()
                name = normalize_space(m.group(2))
            else:
                name = normalize_space(m.group(1))
                ref_no = m.group(2).strip()

            if ref_no in seen:
                continue

            name = re.sub(r"(는|은|을|를|이|가)\s.*$", "", name).strip()
            if len(name) > 35:
                name = name[:35]

            seen.add(ref_no)
            refs.append({
                "ref_no": ref_no,
                "name": name,
                "source_text": m.group(0).strip()
            })

    return refs


# =========================================================
# LLM: 특허 분석 JSON 생성
# =========================================================

EXTRACTION_SYSTEM_PROMPT = """
당신은 특허 명세서를 분석하여 실제 특허도면용 구조 JSON을 만드는 전문가입니다.
반드시 JSON만 출력하세요.

출력 형식:
{
  "invention_type": "hardware|software|method|system|hybrid",
  "main_concept": "발명의 핵심 개념",
  "technical_problem": "해결하려는 기술적 과제",
  "solution_summary": "해결 수단 요약",
  "recommended_diagrams": [
    {
      "fig_number": "도 1",
      "diagram_type": "flowchart|block_diagram|sequence|ui_screen|stateDiagram|concept_diagram",
      "title": "도면 제목",
      "purpose": "도면 목적",
      "source_text": "이 도면을 추천한 근거 문장"
    }
  ],
  "components": [
    {
      "component_id": "100",
      "name": "구성요소명",
      "component_type": "device|process|data|actor|module|database|container|external",
      "description": "역할 설명",
      "source_text": "명세서에서 추출한 근거 문장",
      "relationships": [
        {
          "target": "200",
          "label": "관계 설명",
          "direction": "->",
          "source_text": "관계 근거 문장"
        }
      ]
    }
  ],
  "process_flow": [
    {
      "step_id": "S100",
      "name": "단계명",
      "description": "단계 설명",
      "source_text": "단계 근거 문장"
    }
  ],
  "key_actors": ["사용자", "서버"]
}

중요 규칙:
- source_text 없는 구성요소는 만들지 마세요.
- 명세서에 근거가 없는 임의 구성요소를 만들지 마세요.
- 도면은 최소 2개 권장: 전체 구성도 + 처리 흐름도.
- 도면부호가 있으면 component_id에 그대로 사용하세요.
- 장치/시스템 전체를 나타내는 구성요소는 component_type을 container 또는 device로 설정하세요.
- 사용자, 서버, 외부장치, 단말기, 센서 등 외부와 연결되는 것은 actor 또는 external로 설정하세요.
- 관계를 확신하기 어렵다면 relationships를 비워도 됩니다.
"""


def extract_components(invention_text: str, app_num: str, local_figures: list, local_refs: list) -> dict:
    prompt = f"""
특허 출원번호: {app_num}

[정규식으로 추출된 도면 목록]
{json.dumps(local_figures, ensure_ascii=False, indent=2)}

[정규식으로 추출된 부호 설명]
{json.dumps(local_refs, ensure_ascii=False, indent=2)}

[특허 명세서]
{invention_text[:15000]}

위 정보를 기반으로 추적 가능한 특허 도면 설계 JSON을 생성하세요.
"""
    response = client.chat.completions.create(
        model=MODEL_TEXT,
        max_tokens=5000,
        temperature=0.1,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return safe_json_loads(response.choices[0].message.content)


# =========================================================
# 도면별 fig_json 생성
# =========================================================

def merge_reference_components(analysis: dict, local_refs: list) -> dict:
    components = analysis.get("components", [])
    existing = {str(c.get("component_id", "")).strip() for c in components}

    for ref in local_refs:
        ref_no = str(ref.get("ref_no", "")).strip()
        if not ref_no or ref_no in existing:
            continue
        components.append({
            "component_id": ref_no,
            "name": ref.get("name", ""),
            "component_type": "module",
            "description": ref.get("name", ""),
            "source_text": ref.get("source_text", ""),
            "relationships": []
        })
        existing.add(ref_no)

    analysis["components"] = components
    return analysis


def _component_priority(c: dict) -> int:
    name = str(c.get("name", ""))
    ctype = str(c.get("component_type", ""))
    cid = str(c.get("component_id", ""))
    score = 0
    if ctype in ["container", "device", "external", "actor"]:
        score -= 5
    if any(k in name for k in ["부", "모듈", "서버", "단말", "제어", "처리", "수신", "전송", "생성", "저장"]):
        score -= 3
    if cid.isdigit():
        score -= 2
    return score


def build_fig_design(analysis: dict, diagram_info: dict) -> dict:
    fig_number = diagram_info.get("fig_number", "도 1")
    diagram_type = diagram_info.get("diagram_type", "flowchart")

    components = analysis.get("components", [])
    process_flow = analysis.get("process_flow", [])

    elements = []
    relations = []

    if diagram_type == "flowchart" and process_flow:
        for idx, step in enumerate(process_flow[:MAX_FLOW_STEPS], 1):
            step_id = step.get("step_id") or f"S{idx * 100}"
            elements.append({
                "id": step_id,
                "ref_no": step_id,
                "name": step.get("name", "") or f"처리 단계 {idx}",
                "type": "process",
                "description": step.get("description", ""),
                "source_text": step.get("source_text", "")
            })

        for i in range(len(elements) - 1):
            relations.append({
                "from": elements[i]["id"],
                "to": elements[i + 1]["id"],
                "label": "",
                "source_text": elements[i + 1].get("source_text", "")
            })

    else:
        sorted_components = sorted(components, key=_component_priority)
        selected = sorted_components[:MAX_BLOCK_ELEMENTS]

        for idx, c in enumerate(selected, 1):
            cid = str(c.get("component_id", "")).strip() or f"{idx * 100}"
            node_id = f"N{cid}" if cid and cid[0].isdigit() else (cid or f"N{idx}")
            elements.append({
                "id": node_id,
                "ref_no": cid,
                "name": c.get("name", ""),
                "type": c.get("component_type", "module"),
                "description": c.get("description", ""),
                "source_text": c.get("source_text", "")
            })

        id_map = {str(e["ref_no"]): e["id"] for e in elements}

        for c in selected:
            source_ref = str(c.get("component_id", "")).strip()
            source_id = id_map.get(source_ref)
            if not source_id:
                continue
            for rel in c.get("relationships", []):
                target_ref = str(rel.get("target", "")).strip()
                target_id = id_map.get(target_ref)
                if target_id:
                    relations.append({
                        "from": source_id,
                        "to": target_id,
                        "label": rel.get("label", ""),
                        "source_text": rel.get("source_text", "")
                    })

    return {
        "fig_number": fig_number,
        "title": diagram_info.get("title", ""),
        "diagram_type": diagram_type,
        "purpose": diagram_info.get("purpose", ""),
        "figure_source_text": diagram_info.get("source_text", ""),
        "elements": elements,
        "relations": relations
    }


# =========================================================
# 특허청 스타일 SVG 직접 렌더러
# =========================================================

def normalize_element_type(element_type: str) -> str:
    element_type = str(element_type or "module").strip().lower()
    if element_type in ["user", "actor", "external"]:
        return "actor"
    if element_type in ["db", "database"]:
        return "database"
    if element_type in ["data", "dataset", "file"]:
        return "data"
    if element_type in ["process", "step"]:
        return "process"
    if element_type in ["container", "system"]:
        return "container"
    if element_type in ["device", "hardware"]:
        return "device"
    return "module"


def make_display_name(element: dict) -> str:
    name = normalize_space(element.get("name", ""))
    ref = normalize_space(element.get("ref_no", ""))
    if not name and ref:
        return ref
    if not name:
        return "구성요소"
    return truncate(name, 16)


def is_external_element(element: dict) -> bool:
    name = str(element.get("name", ""))
    t = normalize_element_type(element.get("type", ""))
    external_keywords = [
        "사용자", "단말", "클라이언트", "외부", "관리자", "서버",
        "네트워크", "센서", "카메라", "라이다", "레이더", "차량",
        "디바이스", "입력장치", "표시장치"
    ]
    if t in ["actor"]:
        return True
    return any(k in name for k in external_keywords)


def is_container_candidate(element: dict) -> bool:
    name = str(element.get("name", ""))
    t = normalize_element_type(element.get("type", ""))
    ref = str(element.get("ref_no", ""))
    if t in ["container"]:
        return True
    if is_external_element(element):
        return False
    keywords = ["장치", "시스템", "플랫폼", "서버", "단말", "모듈"]
    return any(k in name for k in keywords) and not ref.startswith("S")


class SvgCanvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.items = []
        self.defs = '''
<defs>
  <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L8,4 L0,8 z" fill="#111"/>
  </marker>
</defs>
'''

    def rect(self, x, y, w, h, stroke="#111", fill="#fff", sw=2, dash=None, rx=0):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" ry="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>'
        )

    def line(self, x1, y1, x2, y2, sw=1.6, dash=None, arrow=False):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        marker = ' marker-end="url(#arrow)"' if arrow else ""
        self.items.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#111" stroke-width="{sw}" fill="none"{dash_attr}{marker}/>'
        )

    def polyline(self, points: List[Tuple[float, float]], sw=1.6, dash=None, arrow=True):
        pts = " ".join([f"{x:.1f},{y:.1f}" for x, y in points])
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        marker = ' marker-end="url(#arrow)"' if arrow else ""
        self.items.append(
            f'<polyline points="{pts}" stroke="#111" stroke-width="{sw}" fill="none"{dash_attr}{marker}/>'
        )

    def text(self, x, y, text, size=18, weight="normal", anchor="middle"):
        self.items.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT_FAMILY}" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" fill="#111">{xml_escape(text)}</text>'
        )

    def multiline_text(self, x, y, text, size=16, weight="normal", anchor="middle", max_chars=10, line_gap=20):
        text = normalize_space(text)
        chunks = []
        cur = ""
        for ch in text:
            cur += ch
            if len(cur) >= max_chars:
                chunks.append(cur)
                cur = ""
        if cur:
            chunks.append(cur)
        if not chunks:
            chunks = [""]

        total_h = (len(chunks[:3]) - 1) * line_gap
        start_y = y - total_h / 2
        for i, line in enumerate(chunks[:3]):
            self.text(x, start_y + i * line_gap, line, size=size, weight=weight, anchor=anchor)

    def label_with_leader(self, tx, ty, target_x, target_y, ref_no: str):
        if not ref_no:
            return
        self.text(tx, ty, ref_no, size=18, weight="bold")
        self.line(tx, ty + 10, target_x, target_y, sw=1.2, arrow=False)

    def block(self, x, y, w, h, name, ref_no="", sw=2, dash=None, font_size=17):
        self.rect(x, y, w, h, sw=sw, dash=dash)
        self.multiline_text(x + w / 2, y + h / 2, name, size=font_size, weight="bold", max_chars=9)
        if ref_no:
            self.label_with_leader(x + w - 8, y - 18, x + w - 15, y + 5, ref_no)

    def to_svg(self) -> str:
        body = "".join(self.items)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
{self.defs}
<rect x="0" y="0" width="{self.width}" height="{self.height}" fill="#ffffff"/>
{body}
</svg>
'''


def split_elements_for_block(elements: list):
    if not elements:
        return None, [], []

    container = next((e for e in elements if is_container_candidate(e)), None)
    rest = [e for e in elements if e is not container]

    external = [e for e in rest if is_external_element(e)]
    internal = [e for e in rest if not is_external_element(e)]

    if not internal and container:
        internal = [container]
        container = None

    internal = internal[:12]
    external = external[:4]
    return container, internal, external


def build_block_layout(fig_json: dict) -> dict:
    elements = fig_json.get("elements", [])
    container, internal, external = split_elements_for_block(elements)

    internal_count = max(1, len(internal))
    rows = math.ceil(internal_count / 3)
    rows = clamp(rows, 1, 4)

    width = 1200
    height = max(760, 260 + rows * 150)

    left_margin = 90
    external_w = 150 if external else 0
    gap = 70 if external else 0
    sys_x = left_margin + external_w + gap
    sys_y = 110
    sys_w = width - sys_x - 90
    sys_h = height - 190

    return {
        "width": width,
        "height": height,
        "sys": (sys_x, sys_y, sys_w, sys_h),
        "container": container,
        "internal": internal,
        "external": external
    }


def render_patent_block_svg(fig_json: dict) -> Tuple[str, dict]:
    layout = build_block_layout(fig_json)
    c = SvgCanvas(layout["width"], layout["height"])

    fig_no = fig_json.get("fig_number", "")
    title = fig_json.get("title", "")
    c.text(layout["width"] / 2, 45, f"{fig_no}  {title}", size=22, weight="bold")

    sys_x, sys_y, sys_w, sys_h = layout["sys"]
    container = layout["container"]
    internal = layout["internal"]
    external = layout["external"]

    container_name = make_display_name(container) if container else "시스템"
    container_ref = container.get("ref_no", "") if container else ""

    c.rect(sys_x, sys_y, sys_w, sys_h, sw=2.2, dash="9 6")
    if container_ref:
        c.label_with_leader(sys_x + sys_w / 2, sys_y - 24, sys_x + sys_w / 2, sys_y, container_ref)
    c.text(sys_x + sys_w / 2, sys_y + 28, container_name, size=20, weight="bold")

    ext_boxes = {}
    if external:
        ext_x = 70
        start_y = sys_y + 100
        step_y = 150
        for i, e in enumerate(external):
            bx = ext_x
            by = start_y + i * step_y
            bw, bh = 150, 90
            c.block(bx, by, bw, bh, make_display_name(e), e.get("ref_no", ""), sw=2.2, font_size=17)
            ext_boxes[e.get("id")] = (bx, by, bw, bh)

    n = len(internal)
    if n == 0:
        internal = [{"id": "N100", "ref_no": "100", "name": "제어부", "type": "module"}]
        n = 1

    cols = 3 if n >= 5 else (2 if n >= 3 else 1)
    rows = math.ceil(n / cols)

    inner_top = sys_y + 95
    inner_left = sys_x + 70
    avail_w = sys_w - 140
    avail_h = sys_h - 145

    box_w = min(210, max(155, (avail_w - (cols - 1) * 60) / cols))
    box_h = 78
    col_gap = (avail_w - cols * box_w) / max(1, cols - 1) if cols > 1 else 0
    row_gap = max(55, (avail_h - rows * box_h) / max(1, rows - 1)) if rows > 1 else 0

    node_boxes = {}

    for idx, e in enumerate(internal):
        r = idx // cols
        col = idx % cols
        offset = 25 if rows >= 3 and r % 2 == 1 and cols > 1 else 0
        x = inner_left + col * (box_w + col_gap) + offset
        y = inner_top + r * (box_h + row_gap)
        x = min(x, sys_x + sys_w - 70 - box_w)
        c.block(x, y, box_w, box_h, make_display_name(e), e.get("ref_no", ""), sw=2.2, font_size=16)
        node_boxes[e.get("id")] = (x, y, box_w, box_h)

    for i in range(len(internal) - 1):
        a = node_boxes.get(internal[i].get("id"))
        b = node_boxes.get(internal[i + 1].get("id"))
        if not a or not b:
            continue
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        same_row = abs(ay - by) < 5
        if same_row:
            c.line(ax + aw, ay + ah / 2, bx, by + bh / 2, sw=1.8, arrow=True)
        else:
            c.polyline([
                (ax + aw / 2, ay + ah),
                (ax + aw / 2, by - 28),
                (bx + bw / 2, by - 28),
                (bx + bw / 2, by)
            ], sw=1.8, arrow=True)

    if external and internal:
        first_box = node_boxes.get(internal[0].get("id"))
        if first_box:
            fx, fy, fw, fh = first_box
            for i, e in enumerate(external[:2]):
                eb = ext_boxes.get(e.get("id"))
                if not eb:
                    continue
                ex, ey, ew, eh = eb
                mid_y = fy + fh / 2 + (i - 0.5) * 18
                c.polyline([
                    (ex + ew, ey + eh / 2),
                    (sys_x - 28, ey + eh / 2),
                    (sys_x - 28, mid_y),
                    (fx, mid_y)
                ], sw=1.7, arrow=True)

    relations = fig_json.get("relations", [])
    drawn = 0
    max_rel = 5
    for rel in relations:
        if drawn >= max_rel:
            break
        a = node_boxes.get(rel.get("from"))
        b = node_boxes.get(rel.get("to"))
        if not a or not b:
            continue
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        if abs(ay - by) < 5:
            continue
        c.polyline([
            (ax + aw, ay + ah / 2),
            (ax + aw + 22, ay + ah / 2),
            (ax + aw + 22, by + bh / 2),
            (bx, by + bh / 2)
        ], sw=1.3, arrow=True)
        drawn += 1

    return c.to_svg(), {
        "layout_type": "patent_block_svg",
        "canvas": {"width": layout["width"], "height": layout["height"]},
        "system_box": layout["sys"],
        "element_count": len(internal) + len(external) + (1 if container else 0),
        "internal_count": len(internal),
        "external_count": len(external)
    }


def render_patent_flow_svg(fig_json: dict) -> Tuple[str, dict]:
    elements = fig_json.get("elements", [])[:MAX_FLOW_STEPS]
    if not elements:
        elements = [{"id": "S100", "ref_no": "S100", "name": "처리 단계", "type": "process"}]

    width = 850
    step_h = 82
    gap = 44
    top = 110
    height = max(760, top + len(elements) * (step_h + gap) + 110)

    c = SvgCanvas(width, height)
    fig_no = fig_json.get("fig_number", "")
    title = fig_json.get("title", "")
    c.text(width / 2, 45, f"{fig_no}  {title}", size=22, weight="bold")
    c.rect(95, 90, width - 190, height - 150, sw=1.7, dash="8 6")

    box_w = 360
    box_h = step_h
    x = (width - box_w) / 2

    boxes = {}
    for i, e in enumerate(elements):
        y = top + i * (step_h + gap)
        c.block(x, y, box_w, box_h, make_display_name(e), "", sw=2.2, font_size=18)
        ref = e.get("ref_no", f"S{(i + 1) * 100}")
        c.label_with_leader(x + box_w + 60, y + 18, x + box_w, y + 18, ref)
        boxes[e.get("id")] = (x, y, box_w, box_h)

    for i in range(len(elements) - 1):
        a = boxes[elements[i].get("id")]
        b = boxes[elements[i + 1].get("id")]
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        c.line(ax + aw / 2, ay + ah, bx + bw / 2, by, sw=2.0, arrow=True)

    return c.to_svg(), {
        "layout_type": "patent_flow_svg",
        "canvas": {"width": width, "height": height},
        "step_count": len(elements)
    }


def render_patent_svg(fig_json: dict, style_template: str = DEFAULT_STYLE_TEMPLATE) -> Tuple[str, dict]:
    diagram_type = fig_json.get("diagram_type", "block_diagram")
    if diagram_type in ["flowchart", "method", "process"]:
        return render_patent_flow_svg(fig_json)
    return render_patent_block_svg(fig_json)


# =========================================================
# 검증기 + 품질 점수
# =========================================================

def validate_fig_json(fig: dict) -> dict:
    errors = []
    warnings = []

    if not fig.get("fig_number"):
        errors.append("fig_number 없음")
    if not fig.get("title"):
        warnings.append("title 없음")

    elements = fig.get("elements", [])
    relations = fig.get("relations", [])
    ids = {e.get("id") for e in elements if e.get("id")}

    if len(elements) < 3:
        warnings.append(f"구성요소가 3개 미만: {len(elements)}개")

    for e in elements:
        if not e.get("id"):
            errors.append("id 없는 element 존재")
        if not e.get("name"):
            warnings.append(f"{e.get('id')} name 없음")
        if not e.get("source_text"):
            warnings.append(f"{e.get('id')} source_text 없음")

    for r in relations:
        if r.get("from") not in ids:
            warnings.append(f"도면에 표시되지 않는 from 노드: {r.get('from')}")
        if r.get("to") not in ids:
            warnings.append(f"도면에 표시되지 않는 to 노드: {r.get('to')}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "element_count": len(elements),
        "relation_count": len(relations)
    }


def score_figure_quality(fig_json: dict, fig_validation: dict, layout_meta: dict) -> dict:
    score = 100
    issues = []
    strengths = []

    elements = fig_json.get("elements", [])
    diagram_type = fig_json.get("diagram_type", "")

    if len(elements) >= 3:
        strengths.append("구성요소 수가 충분합니다.")
    else:
        score -= 15
        issues.append("구성요소가 3개 미만입니다.")

    no_ref = [e for e in elements if not e.get("ref_no")]
    if no_ref:
        score -= min(15, len(no_ref) * 4)
        issues.append(f"도면부호가 없는 구성요소가 {len(no_ref)}개 있습니다.")
    else:
        strengths.append("도면부호 또는 단계부호가 표시됩니다.")

    if layout_meta.get("layout_type") in ["patent_block_svg", "patent_flow_svg"]:
        strengths.append("좌표 기반 특허청 스타일 SVG 렌더링을 사용했습니다.")
    else:
        score -= 15
        issues.append("특허청 스타일 렌더링 메타데이터가 없습니다.")

    if not fig_validation.get("valid"):
        score -= 15
        issues.extend(fig_validation.get("errors", []))

    if diagram_type in ["flowchart", "block_diagram", "sequence", "ui_screen", "stateDiagram", "concept_diagram"]:
        strengths.append("도면 유형이 허용 범위에 있습니다.")
    else:
        score -= 10
        issues.append(f"알 수 없는 도면 유형입니다: {diagram_type}")

    score = max(score, 0)
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"

    return {
        "score": score,
        "grade": grade,
        "pass": score >= QUALITY_PASS_SCORE,
        "issues": issues,
        "strengths": strengths
    }


def make_validation_report(fig_json: dict, layout_meta: dict) -> dict:
    fig_validation = validate_fig_json(fig_json)
    quality = score_figure_quality(fig_json, fig_validation, layout_meta)

    return {
        "valid": fig_validation["valid"],
        "quality": quality,
        "fig_json_validation": fig_validation,
        "layout_meta": layout_meta,
        "created_at": datetime.datetime.now().isoformat()
    }


# =========================================================
# SVG/PNG 변환 + Vision 검수 + 자동 수정 루프
# =========================================================

def export_svg_to_png(svg_path: Path) -> str:
    png_path = str(svg_path).replace(".svg", ".png")

    if CAIROSVG_AVAILABLE:
        try:
            cairosvg.svg2png(url=str(svg_path), write_to=png_path, dpi=220)
            return png_path
        except Exception as e:
            print(f"  [경고] cairosvg PNG 변환 실패: {e}")

    for cmd in [["magick", str(svg_path), png_path], ["convert", str(svg_path), png_path]]:
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                return png_path
            except Exception:
                pass

    print("  [경고] PNG 변환기 없음. SVG만 저장합니다. 필요시: pip install cairosvg")
    return ""


FIG_JSON_REPAIR_SYSTEM_PROMPT = """
당신은 특허 도면 설계 JSON을 개선하는 전문가입니다.
입력된 fig_json의 오류와 품질 이슈를 근거로 fig_json만 수정하세요.
반드시 JSON만 출력하세요.

규칙:
- elements/relation 구조를 유지하세요.
- 도면에 너무 많은 요소가 들어가면 핵심 구성요소 위주로 정리하세요.
- 장치/시스템 전체는 container 또는 device로 설정하세요.
- 사용자, 단말, 외부 서버, 센서 등 외부 개체는 actor 또는 external로 설정하세요.
- source_text는 가능한 기존 문장을 유지하세요.
- SVG나 Mermaid 코드는 작성하지 마세요.
"""


def improve_fig_json_with_feedback(fig_json: dict, validation_result: dict, analysis: dict) -> dict:
    prompt = f"""
[현재 fig_json]
{json.dumps(fig_json, ensure_ascii=False, indent=2)}

[검증/품질 결과]
{json.dumps(validation_result, ensure_ascii=False, indent=2)}

[전체 특허 분석 JSON 참고]
{json.dumps(analysis, ensure_ascii=False, indent=2)[:10000]}

위 정보를 바탕으로 더 나은 fig_json을 JSON만 출력하세요.
"""
    response = client.chat.completions.create(
        model=MODEL_TEXT,
        max_tokens=4000,
        temperature=0.1,
        messages=[
            {"role": "system", "content": FIG_JSON_REPAIR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return safe_json_loads(response.choices[0].message.content)


def run_vision_review_for_generated_png(png_path: str, patent_text: str = "") -> dict:
    if not png_path or not os.path.exists(png_path):
        return {"enabled": False, "reason": "PNG 파일 없음"}

    try:
        images = load_drawing_image(png_path)
        if not images:
            return {"enabled": False, "reason": "이미지 로드 실패"}
        review = analyze_drawing_image(images[0], patent_text=patent_text)
        review["enabled"] = True
        review["source_png"] = png_path
        return review
    except Exception as e:
        return {"enabled": False, "error": str(e)}


# =========================================================
# 리포트 생성
# =========================================================

def save_report(app_dir: Path, app_num: str, results: list):
    scores = [r.quality_score for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0
    pass_count = sum(1 for r in results if r.quality_score >= QUALITY_PASS_SCORE)
    fail_count = len(results) - pass_count

    lines = [
        f"# 도면 생성 리포트 - {app_num}",
        "",
        f"- 생성일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 렌더러: 좌표 기반 특허청 스타일 SVG 직접 렌더러 v5",
        f"- 총 도면 수: {len(results)}",
        f"- 평균 품질 점수: {avg_score:.1f}",
        f"- 통과 기준: {QUALITY_PASS_SCORE}점 이상",
        f"- 통과/검토필요: {pass_count}/{fail_count}",
        "",
        "## 1. 도면별 요약",
        "",
        "| 도면 | 제목 | 유형 | 품질점수 | 등급 | SVG | PNG | Layout |",
        "|---|---|---|---:|---|---|---|---|"
    ]

    for r in results:
        svg_name = Path(r.svg_path).name if r.svg_path else "-"
        png_name = Path(r.png_path).name if r.png_path else "-"
        layout_name = Path(r.layout_path).name if r.layout_path else "-"
        lines.append(
            f"| {r.fig_number} | {r.diagram_title} | {r.diagram_type} | "
            f"{r.quality_score} | {r.quality_grade} | {svg_name} | {png_name} | {layout_name} |"
        )

    lines += [
        "",
        "## 2. 산출물 설명",
        "",
        "| 파일 | 의미 |",
        "|---|---|",
        "| local_extraction.json | 정규식 기반 도면/부호 추출 결과 |",
        "| patent_analysis.json | LLM 기반 전체 발명 분석 JSON |",
        "| figures.json | 생성 대상 도면 목록 |",
        "| *_fig_*.json | 도면별 설계 JSON |",
        "| *_fig_*.svg | 좌표 기반 특허청 스타일 SVG 출력 |",
        "| *_fig_*.png | SVG에서 변환된 PNG 출력 |",
        "| *_fig_*_layout.json | 렌더링 레이아웃 메타데이터 |",
        "| *_fig_*_validation.json | 구조/품질 검증 결과 |",
        "| report.md | 본 리포트 |",
        "",
        "## 3. 참고",
        "",
        "- 본 버전은 Mermaid 자동배치를 사용하지 않고 SVG를 직접 생성합니다.",
        "- 기계 단면도/사시도는 별도 CAD/이미지 생성 렌더러가 필요합니다.",
        "- 현재 버전은 블록도/흐름도/시스템 구성도 실무 스타일에 최적화되어 있습니다.",
        ""
    ]

    with open(app_dir / "report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# =========================================================
# 메인 생성 파이프라인
# =========================================================

def generate_all_drawings(
    invention_text: str,
    app_num: str,
    output_dir: str = "drawing_analysis",
    export_svg: bool = True,
    export_png: bool = True,
    vision_review: bool = False,
    auto_repair: bool = True,
    max_repair_rounds: int = AUTO_REPAIR_DEFAULT_ROUNDS,
    style_template: str = DEFAULT_STYLE_TEMPLATE
) -> list:
    results = []

    app_dir = Path(output_dir) / app_num
    app_dir.mkdir(parents=True, exist_ok=True)

    local_figures = extract_figure_list(invention_text)
    local_refs = extract_reference_numbers(invention_text)

    save_json(app_dir / "local_extraction.json", {
        "figures": local_figures,
        "references": local_refs
    })

    print("  [3.10] 구성 요소 추출 중...")
    analysis = extract_components(invention_text, app_num, local_figures, local_refs)
    analysis = merge_reference_components(analysis, local_refs)
    save_json(app_dir / "patent_analysis.json", analysis)

    print(f"  → 발명 유형: {analysis.get('invention_type')}")
    print(f"  → 핵심 개념: {analysis.get('main_concept')}")

    recommended = analysis.get("recommended_diagrams", [])
    if not recommended:
        recommended = local_figures

    if not recommended:
        recommended = [
            {
                "fig_number": "도 1",
                "diagram_type": "block_diagram",
                "title": "전체 구성도",
                "purpose": "발명의 전체 구성을 표현",
                "source_text": "자동 기본 생성"
            },
            {
                "fig_number": "도 2",
                "diagram_type": "flowchart",
                "title": "처리 흐름도",
                "purpose": "발명의 처리 절차를 표현",
                "source_text": "자동 기본 생성"
            }
        ]

    recommended = recommended[:2]
    save_json(app_dir / "figures.json", {"figures": recommended})

    for diagram_info in recommended:
        fig_num = diagram_info.get("fig_number", "도 1")
        fig_id = fig_num.replace(" ", "_").replace("도", "fig")

        print(f"  [3.11] {fig_num} '{diagram_info.get('title')}' 설계 JSON 생성 중...")
        fig_json = build_fig_design(analysis, diagram_info)

        auto_repaired = False
        repair_rounds = 0

        for attempt in range(max_repair_rounds + 1):
            print(f"  [3.12] {fig_num} 특허청 스타일 SVG 레이아웃 생성 중..." + (f" (수정 {attempt}회차)" if attempt else ""))
            svg_code, layout_meta = render_patent_svg(fig_json, style_template=style_template)
            validation_result = make_validation_report(fig_json, layout_meta)
            quality = validation_result["quality"]

            if not auto_repair:
                break
            if quality["pass"] and validation_result["valid"]:
                break
            if attempt >= max_repair_rounds:
                break

            print(f"  [3.12R] 품질 {quality['score']}점 → fig_json 자동 보정 시도")
            try:
                fig_json = improve_fig_json_with_feedback(fig_json, validation_result, analysis)
                auto_repaired = True
                repair_rounds += 1
            except Exception as e:
                print(f"  [경고] 자동 보정 실패: {e}")
                break

        fig_json_path = app_dir / f"{app_num}_{fig_id}.json"
        save_json(fig_json_path, fig_json)

        layout_path = app_dir / f"{app_num}_{fig_id}_layout.json"
        save_json(layout_path, layout_meta)

        validation_path = app_dir / f"{app_num}_{fig_id}_validation.json"
        save_json(validation_path, validation_result)

        svg_path = app_dir / f"{app_num}_{fig_id}.svg"
        png_path = ""

        if export_svg:
            print(f"  [3.13] {fig_num} SVG 저장 중...")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_code)
        else:
            svg_path = Path("")

        if export_png:
            print(f"  [3.14] {fig_num} PNG 변환 중...")
            png_path = export_svg_to_png(svg_path) if svg_path else ""

        vision_path = ""
        if vision_review:
            print(f"  [4.03] {fig_num} Vision 도면 검수 중...")
            vision_result = run_vision_review_for_generated_png(png_path, patent_text=invention_text)
            vision_path_obj = app_dir / f"{app_num}_{fig_id}_vision.json"
            save_json(vision_path_obj, vision_result)
            vision_path = str(vision_path_obj)

        status = "통과" if quality["pass"] else "검토 필요"

        results.append(
            DrawingResult(
                app_num=app_num,
                fig_number=fig_num,
                diagram_type=fig_json.get("diagram_type", ""),
                diagram_title=fig_json.get("title", ""),
                quality_score=quality["score"],
                quality_grade=quality["grade"],
                fig_json_path=str(fig_json_path),
                svg_path=str(svg_path),
                png_path=png_path,
                layout_path=str(layout_path),
                validation_path=str(validation_path),
                vision_path=vision_path,
                style_template=style_template,
                auto_repaired=auto_repaired,
                repair_rounds=repair_rounds
            )
        )

        print(
            f"  [저장] {svg_path} | 점수 {quality['score']}점 | "
            f"등급 {quality['grade']} | {status}"
        )

    save_json(
        app_dir / f"{app_num}_metadata.json",
        {
            "app_num": app_num,
            "created_at": datetime.datetime.now().isoformat(),
            "renderer": "patent_svg_direct_v5",
            "style_template": style_template,
            "quality_pass_score": QUALITY_PASS_SCORE,
            "auto_repair": auto_repair,
            "max_repair_rounds": max_repair_rounds,
            "export_svg": export_svg,
            "export_png": export_png,
            "vision_review": vision_review,
            "result_count": len(results),
            "results": [asdict(r) for r in results]
        }
    )

    save_report(app_dir, app_num, results)
    return results


# =========================================================
# Vision 분석 기능
# =========================================================

def load_drawing_image(file_path: str) -> list:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일 없음: {file_path}")

    images = []
    ext = file_path.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("PDF 처리를 위해 pdf2image와 poppler가 필요합니다.")
        pages = pdf2image.convert_from_path(file_path, dpi=150)
        for i, page in enumerate(pages):
            buf = io.BytesIO()
            page.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            images.append({
                "fig": f"도 {i + 1}",
                "base64": b64,
                "media_type": "image/png",
                "page": i + 1
            })
    else:
        if not PIL_AVAILABLE:
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
        else:
            img = Image.open(file_path)
            max_side = 2048
            if max(img.size) > max_side:
                ratio = max_side / max(img.size)
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
            buf = io.BytesIO()
            save_format = "PNG" if ext == "png" else "JPEG"
            img.save(buf, format=save_format)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        media_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp"
        }
        images.append({
            "fig": "도 1",
            "base64": b64,
            "media_type": media_map.get(ext, "image/png"),
            "page": 1
        })

    print(f"  [4.01] 이미지 로드 완료: {len(images)}페이지")
    return images


DRAWING_ANALYSIS_SYSTEM = """
당신은 특허 도면 분석 전문가입니다.
업로드된 도면 이미지를 보고 아래 JSON 형식으로만 응답하세요.

{
  "recognized_components": [
    {
      "id": "100",
      "name": "구성요소명",
      "position": "상단|중앙|하단|좌측|우측|좌상|우상|좌하|우하",
      "shape": "사각형|원|다이아몬드|평행사변형|기타",
      "description": "역할 설명"
    }
  ],
  "connections": [
    {
      "from": "100",
      "to": "200",
      "label": "연결 레이블",
      "arrow_type": "실선|점선|양방향|없음"
    }
  ],
  "diagram_type": "flowchart|block_diagram|system_diagram|circuit|mechanism|sequence|class|state|기타",
  "reference_numerals": ["100", "200"],
  "missing_numerals": ["도면부호 없는 구성요소"],
  "issues_found": [
    {
      "severity": "critical|warning|suggestion",
      "location": "도면 내 위치",
      "issue": "문제 내용",
      "rule": "근거",
      "suggestion": "수정 방법"
    }
  ],
  "overall_quality": "excellent|good|fair|poor",
  "completeness_score": 85,
  "strengths": ["잘된 점"],
  "summary": "도면 요약"
}
"""


def analyze_drawing_image(image_data: dict, patent_text: str = "") -> dict:
    user_content = [
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{image_data['media_type']};base64,{image_data['base64']}",
                "detail": "high"
            }
        },
        {
            "type": "text",
            "text": DRAWING_ANALYSIS_SYSTEM + (
                f"\n\n[특허 명세서 참고]\n{patent_text[:3000]}"
                if patent_text else ""
            )
        }
    ]

    response = client.chat.completions.create(
        model=MODEL_VISION,
        max_tokens=3000,
        temperature=0.1,
        messages=[{"role": "user", "content": user_content}]
    )
    return safe_json_loads(response.choices[0].message.content)


def analyze_and_feedback(
    drawing_file: str,
    patent_txt_file: str = "",
    app_num: str = "",
    output_dir: str = "drawing_analysis",
    also_generate: bool = True,
    export_svg: bool = True
):
    if not app_num:
        app_num = Path(drawing_file).stem

    patent_text = ""

    if patent_txt_file and os.path.exists(patent_txt_file):
        parsed = parse_patent_txt(patent_txt_file)
        patent_text = parsed["full"]
        app_num = parsed["app_num"] if not app_num else app_num
        if also_generate:
            generate_all_drawings(patent_text, app_num, output_dir, export_svg=export_svg)

    images = load_drawing_image(drawing_file)
    app_dir = Path(output_dir) / app_num
    app_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for img in images:
        fig = img["fig"]
        fig_id = fig.replace(" ", "_").replace("도", "fig")
        print(f"  [4.02] Vision 분석: {fig}")
        analysis = analyze_drawing_image(img, patent_text)
        out_path = app_dir / f"{app_num}_{fig_id}_vision_analysis.json"
        save_json(out_path, analysis)
        print(f"  [저장] {out_path}")
        results.append(analysis)

    return results


# =========================================================
# 실행 유틸
# =========================================================

def get_txt_files(limit: Optional[int] = None) -> list:
    txt_files = []
    for d in PATENT_DIRS:
        found = glob.glob(f"{d}/*.txt")
        txt_files += found
        print(f"  {d}/: {len(found)}개")

    print(f"  합계: {len(txt_files)}개")

    if limit:
        txt_files = txt_files[:limit]
        print(f"  처리 대상: {len(txt_files)}개")

    return txt_files


def run(
    limit: Optional[int] = None,
    export_svg: bool = True,
    export_png: bool = True,
    vision_review: bool = False,
    auto_repair: bool = True,
    max_repair_rounds: int = AUTO_REPAIR_DEFAULT_ROUNDS,
    style_template: str = DEFAULT_STYLE_TEMPLATE
):
    print("=" * 60)
    print("도면 작성 Agent - 특허청 스타일 SVG 직접 렌더러 v5")
    print("=" * 60)

    txt_files = get_txt_files(limit)
    success = 0
    fail = 0
    skip = 0

    for i, txt_file in enumerate(txt_files, 1):
        print(f"\n[{i}/{len(txt_files)}] {txt_file}")

        try:
            parsed = parse_patent_txt(txt_file)

            if not parsed["claims"] and not parsed["detail"]:
                print("  [스킵] 청구범위/설명 없음")
                skip += 1
                continue

            results = generate_all_drawings(
                invention_text=parsed["full"],
                app_num=parsed["app_num"],
                output_dir="drawing_analysis",
                export_svg=export_svg,
                export_png=export_png,
                vision_review=vision_review,
                auto_repair=auto_repair,
                max_repair_rounds=max_repair_rounds,
                style_template=style_template
            )

            if results:
                avg_score = sum(r.quality_score for r in results) / len(results)
                print(f"  ✅ 완료: {len(results)}개 도면 | 평균 점수 {avg_score:.1f}")
                success += 1
            else:
                print("  [실패] 도면 생성 안됨")
                fail += 1

        except KeyboardInterrupt:
            print("\n[중단] 사용자에 의해 실행이 중단되었습니다.")
            break
        except Exception as e:
            print(f"  [오류] {e}")
            fail += 1

    print("\n" + "=" * 60)
    print(f"배치 완료: 성공 {success} | 실패 {fail} | 스킵 {skip}")
    print("=" * 60)


def test_with_sample(
    export_svg: bool = True,
    export_png: bool = True,
    vision_review: bool = False,
    auto_repair: bool = True,
    style_template: str = DEFAULT_STYLE_TEMPLATE
):
    sample = """
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

    results = generate_all_drawings(
        sample,
        "TEST-001",
        "drawing_analysis",
        export_svg=export_svg,
        export_png=export_png,
        vision_review=vision_review,
        auto_repair=auto_repair,
        style_template=style_template
    )

    print(f"\n✅ 생성된 도면: {len(results)}개")
    for r in results:
        print(f"  - {r.fig_number}: {r.quality_score}점/{r.quality_grade} | {r.svg_path}")


def test_with_real_file(
    export_svg: bool = True,
    export_png: bool = True,
    vision_review: bool = False,
    auto_repair: bool = True,
    style_template: str = DEFAULT_STYLE_TEMPLATE
):
    txt_files = get_txt_files(limit=1)

    if not txt_files:
        print("[경고] txt 파일 없음 → 샘플 테스트 실행")
        test_with_sample(
            export_svg=export_svg,
            export_png=export_png,
            vision_review=vision_review,
            auto_repair=auto_repair,
            style_template=style_template
        )
        return

    parsed = parse_patent_txt(txt_files[0])
    results = generate_all_drawings(
        parsed["full"],
        parsed["app_num"],
        "drawing_analysis",
        export_svg=export_svg,
        export_png=export_png,
        vision_review=vision_review,
        auto_repair=auto_repair,
        style_template=style_template
    )

    print(f"\n✅ 생성된 도면: {len(results)}개")
    for r in results:
        print(f"  - {r.fig_number}: {r.quality_score}점/{r.quality_grade} | {r.svg_path}")


# =========================================================
# CLI
# =========================================================

if __name__ == "__main__":
    import sys

    HELP = """
사용법:
  python drawing_agent.py test
  python drawing_agent.py test --vision
  python drawing_agent.py real
  python drawing_agent.py run 10
  python drawing_agent.py run 10 --vision
  python drawing_agent.py run 10 --no-svg --no-png
  python drawing_agent.py analyze <이미지_or_pdf>
  python drawing_agent.py analyze <이미지_or_pdf> <특허_txt>

옵션:
  --vision              생성된 PNG를 Vision으로 검수
  --no-svg              SVG 자동 생성 끄기
  --no-png              PNG 자동 생성 끄기
  --no-repair           낮은 점수 도면 자동 수정 끄기
  --repair-rounds N     자동 수정 반복 횟수, 기본 1
  --style NAME          patent_office
"""

    args = sys.argv[1:]

    vision_review = "--vision" in args
    export_svg = "--no-svg" not in args
    export_png = "--no-png" not in args or vision_review
    auto_repair = "--no-repair" not in args
    style_template = DEFAULT_STYLE_TEMPLATE
    max_repair_rounds = AUTO_REPAIR_DEFAULT_ROUNDS

    if "--style" in args:
        idx = args.index("--style")
        if idx + 1 < len(args):
            style_template = args[idx + 1]

    if "--repair-rounds" in args:
        idx = args.index("--repair-rounds")
        if idx + 1 < len(args):
            max_repair_rounds = int(args[idx + 1])

    cleaned = []
    skip_next = False
    for idx, a in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if a in ["--vision", "--no-svg", "--no-png", "--no-repair"]:
            continue
        if a in ["--style", "--repair-rounds"]:
            skip_next = True
            continue
        cleaned.append(a)
    args = cleaned

    if not args or args[0] == "test":
        test_with_sample(
            export_svg=export_svg,
            export_png=export_png,
            vision_review=vision_review,
            auto_repair=auto_repair,
            style_template=style_template
        )

    elif args[0] == "real":
        test_with_real_file(
            export_svg=export_svg,
            export_png=export_png,
            vision_review=vision_review,
            auto_repair=auto_repair,
            style_template=style_template
        )

    elif args[0] == "run":
        limit = int(args[1]) if len(args) > 1 else None
        run(
            limit,
            export_svg=export_svg,
            export_png=export_png,
            vision_review=vision_review,
            auto_repair=auto_repair,
            max_repair_rounds=max_repair_rounds,
            style_template=style_template
        )

    elif args[0] == "analyze":
        if len(args) < 2:
            print(HELP)
            sys.exit(1)

        drawing_file = args[1]
        patent_txt = args[2] if len(args) > 2 else ""

        analyze_and_feedback(
            drawing_file,
            patent_txt,
            export_svg=export_svg
        )

    else:
        print(HELP)
