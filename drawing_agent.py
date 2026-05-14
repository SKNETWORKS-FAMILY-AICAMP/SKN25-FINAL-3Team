# drawing_agent.py - 특허청 실무 도면 품질 SVG 렌더러 v7
# 변리사/도면사 수준의 도면 생성
#
# 흐름도: 타원(시작/종료) + 마름모(판단) + 사각형(처리) + 평행사변형(입출력)
# 블록도: 점선 시스템 경계 + 계층 구조 + 깔끔한 인출선
# 시퀀스: 활성화 박스 + 동기/비동기 화살표 + 자기루프
# 상태도: 둥근 사각형 노드 + 초기/종료 마커 + 곡선 전이
# UI도:  디바이스 프레임 + 타입별 UI 요소
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
from typing import Optional, List, Tuple, Dict
from dotenv import load_dotenv
from openai import OpenAI

try:
    import base64
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import cairosvg
    CAIROSVG_AVAILABLE = True
except Exception:
    CAIROSVG_AVAILABLE = False

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_TEXT  = "gpt-4o-mini"
MODEL_VISION = "gpt-4o"

PATENT_DIRS            = ["G06F", "G06N", "G06Q", "G06V"]
QUALITY_PASS_SCORE     = 75
AUTO_REPAIR_ROUNDS     = 1
DEFAULT_STYLE          = "patent_office"
MAX_BLOCK_ELEMENTS     = 14
MAX_FLOW_STEPS         = 14
FONT                   = "NanumGothic, Noto Sans CJK KR, Noto Sans KR, Malgun Gothic, Arial, sans-serif"


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
    style_template: str = DEFAULT_STYLE
    auto_repaired: bool = False
    repair_rounds: int = 0


# ─────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────

def safe_json(raw: str) -> dict:
    raw = re.sub(r"```json\s*|\s*```", "", str(raw).strip()).strip()
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            return json.loads(m.group())
    raise ValueError("JSON 파싱 실패")

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ns(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()

def xe(s: str) -> str:
    return str(s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def clamp(v, lo, hi): return max(lo, min(hi, v))

def trunc(text: str, n: int = 20) -> str:
    text = ns(text)
    return text if len(text) <= n else text[:n-1] + "…"

def is_decision(name: str, step_type: str = "") -> bool:
    if step_type == "decision":
        return True
    kw = ["판단", "확인", "검사", "여부", "인지", "확인하", "결정", "선택", "검증", "체크", "비교"]
    return any(k in name for k in kw)

def is_terminal(name: str, step_type: str = "", idx: int = -1, total: int = 0) -> bool:
    if step_type == "terminal":
        return True
    if idx == 0 and any(k in name for k in ["시작", "START", "start", "begin", "Begin"]):
        return True
    if idx == total - 1 and any(k in name for k in ["종료", "END", "end", "완료", "finish", "Finish"]):
        return True
    return False


# ─────────────────────────────────────────
# 특허 파싱
# ─────────────────────────────────────────

def extract_section(text, starts, ends):
    start = -1
    for kw in starts:
        idx = text.find(kw)
        if idx != -1:
            start = idx; break
    if start == -1:
        return ""
    ends_found = [text.find(kw, start+1) for kw in ends if text.find(kw, start+1) != -1]
    end = min(ends_found) if ends_found else start + 6000
    return text[start:end].strip()

def parse_patent_txt(txt_file: str) -> dict:
    with open(txt_file, "r", encoding="utf-8-sig") as f:
        text = f.read()
    app_num = os.path.basename(txt_file).replace(".txt", "")
    claims    = extract_section(text, ["청구범위"], ["발명의 설명","요약","도면의 간단한 설명"])
    detail    = extract_section(text, ["발명의 설명","발명의 상세한 설명","상세한 설명"], ["청구범위"])
    fig_desc  = extract_section(text, ["도면의 간단한 설명"], ["발명을 실시하기 위한","발명의 효과","부호의 설명"])
    ref_desc  = extract_section(text, ["부호의 설명"], ["청구범위","요약","산업상"])
    full = f"[청구범위]\n{claims}\n\n[도면의 간단한 설명]\n{fig_desc}\n\n[부호의 설명]\n{ref_desc}\n\n[발명의 상세한 설명]\n{detail}".strip()
    return {"app_num": app_num, "claims": claims, "detail": detail,
            "figure_desc": fig_desc, "reference_desc": ref_desc, "full": full}

def classify_type(title: str) -> str:
    t = title or ""
    if any(k in t for k in ["순서도","흐름도","플로우","과정","절차","방법","단계"]): return "flowchart"
    if any(k in t for k in ["구성도","시스템","장치","블록도","구조도","모듈"]):     return "block_diagram"
    if any(k in t for k in ["화면","UI","인터페이스","표시"]):                        return "ui_screen"
    if any(k in t for k in ["시퀀스","상호작용","통신","메시지"]):                   return "sequence"
    if any(k in t for k in ["상태"]):                                                 return "stateDiagram"
    return "block_diagram"

def extract_figure_list(text: str) -> list:
    figs, seen = [], set()
    for pat in [r"도\s*(\d+[A-Za-z]?)\s*(?:은|는)\s*([^\n\.]+)",
                r"\[도\s*(\d+[A-Za-z]?)\]\s*([^\n]+)",
                r"도\s*(\d+[A-Za-z]?)\s*[:：]\s*([^\n]+)"]:
        for m in re.finditer(pat, text):
            fn = f"도 {m.group(1)}"
            if fn in seen: continue
            seen.add(fn)
            title = ns(m.group(2))
            figs.append({"fig_number": fn, "title": title,
                         "diagram_type": classify_type(title),
                         "purpose": title, "source_text": m.group(0).strip()})
    figs.sort(key=lambda x: int(re.findall(r"\d+", x["fig_number"])[0]) if re.findall(r"\d+", x["fig_number"]) else 9999)
    return figs

def extract_refs(text: str) -> list:
    refs, seen = [], set()
    for pat in [r"(\d{2,5})\s*[:：]\s*([^\n,;]+)",
                r"(\d{2,5})\s*[\.]\s*([^\n,;]+)",
                r"(\d{2,5})\s*[-–]\s*([^\n,;]+)",
                r"([가-힣A-Za-z0-9\s]+)\((\d{2,5})\)"]:
        for m in re.finditer(pat, text):
            if m.group(1).isdigit():
                ref_no, name = m.group(1).strip(), ns(m.group(2))
            else:
                name, ref_no = ns(m.group(1)), m.group(2).strip()
            if ref_no in seen: continue
            name = re.sub(r"(는|은|을|를|이|가)\s.*$", "", name).strip()[:35]
            seen.add(ref_no)
            refs.append({"ref_no": ref_no, "name": name, "source_text": m.group(0).strip()})
    return refs


# ─────────────────────────────────────────
# LLM 분석 프롬프트 (step_type 포함)
# ─────────────────────────────────────────

SYSTEM_PROMPT = """
당신은 특허 명세서를 분석하여 특허 도면 설계 JSON을 만드는 전문가입니다.
반드시 JSON만 출력하세요.

{
  "invention_type": "hardware|software|method|system|hybrid",
  "main_concept": "발명의 핵심 개념",
  "technical_problem": "해결하려는 기술적 과제",
  "solution_summary": "해결 수단 요약",
  "recommended_diagrams": [
    {
      "fig_number": "도 1",
      "diagram_type": "flowchart|block_diagram|sequence|ui_screen|stateDiagram",
      "title": "도면 제목",
      "purpose": "목적",
      "source_text": "근거 문장"
    }
  ],
  "components": [
    {
      "component_id": "100",
      "name": "구성요소명",
      "component_type": "device|process|data|actor|module|database|container|external",
      "description": "역할",
      "source_text": "근거",
      "relationships": [
        {"target": "200", "label": "관계", "direction": "->", "source_text": "근거"}
      ]
    }
  ],
  "process_flow": [
    {
      "step_id": "S100",
      "step_type": "terminal|process|decision|io",
      "name": "단계명",
      "description": "설명",
      "source_text": "근거",
      "branches": [
        {"label": "예", "target": "S200"},
        {"label": "아니오", "target": "S300"}
      ]
    }
  ],
  "key_actors": ["사용자", "서버"]
}

step_type 규칙:
- terminal: 시작/종료 단계 (첫 번째, 마지막 단계)
- process: 일반 처리 단계
- decision: 조건 판단, 여부 확인, 검사 단계 (branches 필수)
- io: 입력/출력/수신/전송 단계

중요:
- source_text 없는 구성요소 만들지 말것
- 도면은 최소 2개: 전체구성도 + 처리흐름도
- 흐름도는 반드시 시작(terminal) → 처리(process/decision/io) → 종료(terminal) 순서
- 구성요소(components)는 명세서에 언급된 모든 핵심 구성요소를 빠짐없이 추출할 것 (최소 5개 이상)
- 각 구성요소의 name은 원문 그대로 사용하고 축약하지 말 것
- decision 단계는 branches에 예/아니오 또는 성공/실패 등 분기 명시
"""

def extract_components(text: str, app_num: str, local_figs: list, local_refs: list) -> dict:
    prompt = f"""
특허 출원번호: {app_num}

[도면 목록]
{json.dumps(local_figs, ensure_ascii=False, indent=2)}

[부호 설명]
{json.dumps(local_refs, ensure_ascii=False, indent=2)}

[특허 명세서]
{text[:15000]}
"""
    resp = client.chat.completions.create(
        model=MODEL_TEXT, max_tokens=5000, temperature=0.1,
        messages=[{"role":"system","content":SYSTEM_PROMPT},
                  {"role":"user","content":prompt}]
    )
    return safe_json(resp.choices[0].message.content)

def merge_refs(analysis: dict, local_refs: list) -> dict:
    comps = analysis.get("components", [])
    existing = {str(c.get("component_id","")).strip() for c in comps}
    for ref in local_refs:
        rn = str(ref.get("ref_no","")).strip()
        if not rn or rn in existing: continue
        comps.append({"component_id": rn, "name": ref.get("name",""),
                      "component_type": "module", "description": ref.get("name",""),
                      "source_text": ref.get("source_text",""), "relationships": []})
        existing.add(rn)
    analysis["components"] = comps
    return analysis

def comp_priority(c: dict) -> int:
    name, ctype, cid = str(c.get("name","")), str(c.get("component_type","")), str(c.get("component_id",""))
    score = 0
    if ctype in ["container","device","external","actor"]: score -= 5
    if any(k in name for k in ["부","모듈","서버","단말","제어","처리","수신","전송","생성","저장"]): score -= 3
    if cid.isdigit(): score -= 2
    return score


# ─────────────────────────────────────────
# fig_json 설계
# ─────────────────────────────────────────

def build_fig_design(analysis: dict, diagram_info: dict) -> dict:
    dtype = diagram_info.get("diagram_type", "block_diagram")
    comps = analysis.get("components", [])
    flow  = analysis.get("process_flow", [])
    elements, relations = [], []

    if dtype == "flowchart":
        n = len(flow)
        for idx, step in enumerate(flow[:MAX_FLOW_STEPS]):
            sid = step.get("step_id") or f"S{(idx+1)*100}"
            stype = step.get("step_type", "process")
            # 자동 판단
            if is_terminal(step.get("name",""), stype, idx, n): stype = "terminal"
            elif is_decision(step.get("name",""), stype):        stype = "decision"
            elements.append({
                "id": sid, "ref_no": sid,
                "name": step.get("name","") or f"단계 {idx+1}",
                "shape_type": stype,
                "description": step.get("description",""),
                "source_text": step.get("source_text",""),
                "branches": step.get("branches", [])
            })
        for i in range(len(elements)-1):
            relations.append({"from": elements[i]["id"], "to": elements[i+1]["id"], "label": ""})

    elif dtype == "sequence":
        actors = analysis.get("key_actors", [])
        if not actors: actors = ["클라이언트","서버"]
        for idx, a in enumerate(actors[:6]):
            elements.append({"id": f"A{idx}", "ref_no": f"A{idx}",
                             "name": a, "type": "actor", "description":"", "source_text":""})
        for idx, step in enumerate(flow[:12], 1):
            from_i = (idx-1) % max(1, len(actors)-1)
            to_i   = idx % len(actors)
            relations.append({
                "from": f"A{from_i}", "to": f"A{to_i}",
                "label": step.get("name", f"메시지 {idx}"),
                "msg_type": "sync" if idx % 3 != 0 else "async",
                "source_text": step.get("source_text","")
            })

    elif dtype == "stateDiagram":
        sorted_c = sorted(comps, key=comp_priority)[:8]
        for idx, c in enumerate(sorted_c, 1):
            cid = str(c.get("component_id","")).strip() or f"{idx*100}"
            elements.append({"id": f"ST{cid}", "ref_no": cid,
                             "name": c.get("name",""), "type": "state",
                             "description": c.get("description",""),
                             "source_text": c.get("source_text","")})
        id_map = {str(e["ref_no"]): e["id"] for e in elements}
        for c in sorted_c:
            src = id_map.get(str(c.get("component_id","")).strip())
            if not src: continue
            for rel in c.get("relationships",[]):
                tgt = id_map.get(str(rel.get("target","")).strip())
                if tgt:
                    relations.append({"from": src, "to": tgt,
                                      "label": rel.get("label",""),
                                      "source_text": rel.get("source_text","")})

    elif dtype == "ui_screen":
        sorted_c = sorted(comps, key=comp_priority)[:10]
        for idx, c in enumerate(sorted_c, 1):
            cid = str(c.get("component_id","")).strip() or f"{idx*100}"
            elements.append({"id": f"UI{cid}", "ref_no": cid,
                             "name": c.get("name",""),
                             "type": c.get("component_type","module"),
                             "description": c.get("description",""),
                             "source_text": c.get("source_text","")})
    else:
        # block_diagram / concept_diagram
        sorted_c = sorted(comps, key=comp_priority)[:MAX_BLOCK_ELEMENTS]
        for idx, c in enumerate(sorted_c, 1):
            cid = str(c.get("component_id","")).strip() or f"{idx*100}"
            nid = f"N{cid}" if cid and cid[0].isdigit() else (cid or f"N{idx}")
            elements.append({"id": nid, "ref_no": cid,
                             "name": c.get("name",""),
                             "type": c.get("component_type","module"),
                             "description": c.get("description",""),
                             "source_text": c.get("source_text","")})
        id_map = {str(e["ref_no"]): e["id"] for e in elements}
        for c in sorted_c:
            src = id_map.get(str(c.get("component_id","")).strip())
            if not src: continue
            for rel in c.get("relationships",[]):
                tgt = id_map.get(str(rel.get("target","")).strip())
                if tgt:
                    relations.append({"from": src, "to": tgt,
                                      "label": rel.get("label",""),
                                      "source_text": rel.get("source_text","")})

    return {"fig_number": diagram_info.get("fig_number","도 1"),
            "title": diagram_info.get("title",""),
            "diagram_type": dtype,
            "purpose": diagram_info.get("purpose",""),
            "figure_source_text": diagram_info.get("source_text",""),
            "elements": elements, "relations": relations}


# ─────────────────────────────────────────
# SVG 캔버스
# ─────────────────────────────────────────

class SvgCanvas:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.items: List[str] = []
        self.defs = '''<defs>
  <marker id="arr" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L9,4.5 L0,9 z" fill="#111"/>
  </marker>
  <marker id="arr-open" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="strokeWidth">
    <path d="M0,1 L8,4.5 L0,8" fill="none" stroke="#111" stroke-width="1.3"/>
  </marker>
  <marker id="arr-dash" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L9,4.5 L0,9 z" fill="#555"/>
  </marker>
</defs>'''

    def rect(self, x,y,w,h, stroke="#111",fill="#fff",sw=2,dash=None,rx=0):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" ry="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{da}/>')

    def diamond(self, cx,cy,w,h, stroke="#111",fill="#fff",sw=2):
        pts = f"{cx:.1f},{(cy-h/2):.1f} {(cx+w/2):.1f},{cy:.1f} {cx:.1f},{(cy+h/2):.1f} {(cx-w/2):.1f},{cy:.1f}"
        self.items.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def oval(self, cx,cy,w,h, stroke="#111",fill="#fff",sw=2):
        self.items.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w/2:.1f}" ry="{h/2:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def parallelogram(self, x,y,w,h, stroke="#111",fill="#fff",sw=2):
        sk = 18
        pts = f"{x+sk:.1f},{y:.1f} {x+w:.1f},{y:.1f} {x+w-sk:.1f},{y+h:.1f} {x:.1f},{y+h:.1f}"
        self.items.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, cx,cy,r, stroke="#111",fill="#fff",sw=2):
        self.items.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def line(self, x1,y1,x2,y2, sw=1.7,dash=None,arrow=True,marker="arr"):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        mk = f' marker-end="url(#{marker})"' if arrow else ""
        self.items.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#111" stroke-width="{sw}" fill="none"{da}{mk}/>')

    def polyline(self, pts: List[Tuple[float,float]], sw=1.7,dash=None,arrow=True,marker="arr"):
        ps = " ".join([f"{x:.1f},{y:.1f}" for x,y in pts])
        da = f' stroke-dasharray="{dash}"' if dash else ""
        mk = f' marker-end="url(#{marker})"' if arrow else ""
        self.items.append(
            f'<polyline points="{ps}" stroke="#111" stroke-width="{sw}" fill="none"{da}{mk}/>')

    def path(self, d:str, sw=1.7,dash=None,arrow=True,fill="none",marker="arr",stroke="#111"):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        mk = f' marker-end="url(#{marker})"' if arrow else ""
        self.items.append(
            f'<path d="{d}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}"{da}{mk}/>')

    def text(self, x,y,t,size=17,weight="normal",anchor="middle",fill="#111"):
        self.items.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" dominant-baseline="middle" '
            f'fill="{fill}">{xe(t)}</text>')

    def mtext(self, x,y,t,size=15,weight="normal",anchor="middle",max_ch=9,gap=19):
        """여러 줄 텍스트"""
        t = ns(t)
        chunks, cur = [], ""
        for ch in t:
            cur += ch
            if len(cur) >= max_ch:
                chunks.append(cur); cur = ""
        if cur: chunks.append(cur)
        if not chunks: chunks = [""]
        total = (len(chunks[:3])-1)*gap
        sy = y - total/2
        for i, line in enumerate(chunks[:3]):
            self.text(x, sy+i*gap, line, size=size, weight=weight, anchor=anchor)

    def leader(self, tx,ty, lx,ly, ref:str, size=16):
        """도면부호 인출선"""
        if not ref: return
        self.text(tx, ty, ref, size=size, weight="bold")
        # 수평 인출선
        self.line(tx, ty+size*0.6, lx, ly, sw=1.0, arrow=False)

    def to_svg(self) -> str:
        body = "".join(self.items)
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">\n{self.defs}\n'
                f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#ffffff"/>\n'
                f'{body}\n</svg>')


# ─────────────────────────────────────────
# 렌더러 1: 흐름도 (변리사 실무 수준)
# ─────────────────────────────────────────

def render_flowchart(fig_json: dict) -> Tuple[str, dict]:
    elements = fig_json.get("elements", [])[:MAX_FLOW_STEPS]
    if not elements:
        elements = [
            {"id":"S100","ref_no":"S100","name":"시작","shape_type":"terminal","branches":[]},
            {"id":"S200","ref_no":"S200","name":"처리","shape_type":"process","branches":[]},
            {"id":"S300","ref_no":"S300","name":"종료","shape_type":"terminal","branches":[]},
        ]

    # 크기 정의
    PROC_W, PROC_H    = 340, 72
    OVAL_W, OVAL_H    = 280, 60
    DIAM_W, DIAM_H    = 320, 90
    IO_W,   IO_H      = 320, 65
    V_GAP             = 48       # 세로 간격
    MAIN_X            = 480      # 메인 흐름 중심 X
    BRANCH_X_OFFSET   = 320      # 판단 분기 오른쪽 오프셋

    # 높이 계산
    total_h = 110
    for e in elements:
        st = e.get("shape_type","process")
        if st == "terminal":  total_h += OVAL_H + V_GAP
        elif st == "decision": total_h += DIAM_H + V_GAP
        elif st == "io":       total_h += IO_H + V_GAP
        else:                  total_h += PROC_H + V_GAP
    total_h += 80
    height = max(900, total_h)
    width  = 960

    c = SvgCanvas(width, height)
    fig_no = fig_json.get("fig_number","")
    title  = fig_json.get("title","")
    c.text(width/2, 42, f"{fig_no}  {title}", size=22, weight="bold")
    c.rect(55, 72, width-110, height-100, sw=1.5, dash="8 5")

    # 각 요소의 y 좌표와 크기 저장
    box_info: Dict[str, dict] = {}  # id → {x,y,w,h,shape_type,cx,cy,bottom,top}
    y = 110

    for e in elements:
        eid = e.get("id","")
        st  = e.get("shape_type","process")
        name = trunc(e.get("name",""), 14)
        ref  = e.get("ref_no","")
        cx   = MAIN_X

        if st == "terminal":
            w, h = OVAL_W, OVAL_H
            x = cx - w/2
            c.oval(cx, y+h/2, w, h, sw=2.4)
            c.mtext(cx, y+h/2, name, size=17, weight="bold", max_ch=10)
            if ref: c.leader(cx+w/2+55, y+10, cx+w/2, y+h/2, ref)
            box_info[eid] = {"cx":cx,"cy":y+h/2,"top":y,"bottom":y+h,"w":w,"h":h,"shape":"oval"}

        elif st == "decision":
            w, h = DIAM_W, DIAM_H
            x = cx - w/2
            mid_y = y + h/2
            c.diamond(cx, mid_y, w, h, sw=2.2)
            c.mtext(cx, mid_y, name, size=15, weight="bold", max_ch=9, gap=17)
            if ref: c.leader(cx+w/2+55, y+10, cx+w/2, mid_y, ref)
            box_info[eid] = {"cx":cx,"cy":mid_y,"top":y,"bottom":y+h,"w":w,"h":h,"shape":"diamond"}

        elif st == "io":
            w, h = IO_W, IO_H
            x = cx - w/2
            c.parallelogram(x, y, w, h, sw=2.0)
            c.mtext(cx, y+h/2, name, size=16, weight="bold", max_ch=11)
            if ref: c.leader(x+w+55, y+8, x+w, y+h/2, ref)
            box_info[eid] = {"cx":cx,"cy":y+h/2,"top":y,"bottom":y+h,"w":w,"h":h,"shape":"para"}

        else:  # process
            w, h = PROC_W, PROC_H
            x = cx - w/2
            c.rect(x, y, w, h, sw=2.2)
            c.mtext(cx, y+h/2, name, size=17, weight="bold", max_ch=10)
            if ref: c.leader(x+w+55, y+10, x+w, y+h/2, ref)
            box_info[eid] = {"cx":cx,"cy":y+h/2,"top":y,"bottom":y+h,"w":w,"h":h,"shape":"rect"}

        if st == "terminal": y += OVAL_H + V_GAP
        elif st == "decision": y += DIAM_H + V_GAP
        elif st == "io":     y += IO_H + V_GAP
        else:                y += PROC_H + V_GAP

    # 연결선 그리기
    for i, e in enumerate(elements[:-1]):
        eid  = e.get("id","")
        neid = elements[i+1].get("id","")
        bi   = box_info.get(eid)
        bn   = box_info.get(neid)
        if not bi or not bn: continue

        st = e.get("shape_type","process")
        branches = e.get("branches",[])

        if st == "decision" and len(branches) >= 2:
            # 주 흐름: 예 → 아래
            lbl_yes = branches[0].get("label","예") if branches else "예"
            lbl_no  = branches[1].get("label","아니오") if len(branches)>1 else "아니오"
            # 아래 화살표 (예)
            c.line(bi["cx"], bi["bottom"], bn["cx"], bn["top"], sw=1.8)
            c.text(bi["cx"]+14, (bi["bottom"]+bn["top"])/2, lbl_yes, size=14, anchor="start", fill="#333")
            # 오른쪽 분기 (아니오) - 점선으로 표시
            bx = bi["cx"] + DIAM_W/2
            c.polyline([(bx, bi["cy"]),
                        (bx+80, bi["cy"]),
                        (bx+80, bn["cy"]),
                        (bn["cx"]+PROC_W/2, bn["cy"])],
                       sw=1.4, dash="5 3", arrow=False)
            c.text(bx+40, bi["cy"]-14, lbl_no, size=13, anchor="middle", fill="#666")
        else:
            # 일반 연결: 아래로
            c.line(bi["cx"], bi["bottom"], bn["cx"], bn["top"], sw=1.8)

    return c.to_svg(), {
        "layout_type": "patent_flow_pro",
        "canvas": {"width": width, "height": height},
        "step_count": len(elements),
        "decision_count": sum(1 for e in elements if e.get("shape_type")=="decision")
    }


# ─────────────────────────────────────────
# 렌더러 2: 블록도
# ─────────────────────────────────────────

def _is_external(e: dict) -> bool:
    name = str(e.get("name",""))
    t = str(e.get("type",""))
    if t in ["actor","external"]: return True
    return any(k in name for k in ["사용자","단말","클라이언트","외부","관리자","네트워크","센서","카메라"])

def _is_container(e: dict) -> bool:
    name = str(e.get("name",""))
    t = str(e.get("type",""))
    if t in ["container"]: return True
    if _is_external(e): return False
    return any(k in name for k in ["장치","시스템","플랫폼","서버","단말","모듈"])

def render_block_diagram(fig_json: dict) -> Tuple[str, dict]:
    elements = fig_json.get("elements", [])
    relations = fig_json.get("relations", [])

    container = next((e for e in elements if _is_container(e)), None)
    rest      = [e for e in elements if e is not container]
    external  = [e for e in rest if _is_external(e)][:4]
    internal  = [e for e in rest if not _is_external(e)][:12]
    if not internal and container:
        internal, container = [container], None

    n    = max(1, len(internal))
    cols = 3 if n >= 5 else (2 if n >= 3 else 1)
    rows = math.ceil(n / cols)

    width  = 1200
    height = max(780, 260 + rows * 155)

    EXT_W = 160 if external else 0
    SYS_X = 110 + EXT_W + (60 if external else 0)
    SYS_Y = 105
    SYS_W = width - SYS_X - 85
    SYS_H = height - 185

    c = SvgCanvas(width, height)
    fig_no = fig_json.get("fig_number","")
    title  = fig_json.get("title","")
    c.text(width/2, 42, f"{fig_no}  {title}", size=22, weight="bold")

    # 시스템 경계 (점선 사각형)
    c.rect(SYS_X, SYS_Y, SYS_W, SYS_H, sw=2.0, dash="10 5")
    cname = trunc(container.get("name","시스템") if container else "시스템", 16)
    cref  = container.get("ref_no","") if container else ""
    c.text(SYS_X+SYS_W/2, SYS_Y+26, cname, size=20, weight="bold")
    if cref: c.leader(SYS_X+SYS_W/2, SYS_Y-22, SYS_X+SYS_W/2, SYS_Y, cref)

    # 외부 엔티티
    ext_boxes: Dict[str, tuple] = {}
    for i, e in enumerate(external):
        bx, by, bw, bh = 70, SYS_Y+90+i*155, EXT_W, 85
        c.rect(bx, by, bw, bh, sw=2.2, rx=4)
        c.mtext(bx+bw/2, by+bh/2, trunc(e.get("name",""),10), size=16, weight="bold", max_ch=7)
        ref = e.get("ref_no","")
        if ref: c.leader(bx+bw+50, by+8, bx+bw, by+bh/2, ref)
        ext_boxes[e.get("id","")] = (bx, by, bw, bh)

    # 내부 구성요소
    INNER_TOP  = SYS_Y + 85
    INNER_LEFT = SYS_X + 60
    AVAIL_W    = SYS_W - 120
    AVAIL_H    = SYS_H - 130
    BOX_W = min(215, max(150, (AVAIL_W-(cols-1)*55)/cols))
    BOX_H = 75
    COL_GAP = (AVAIL_W-cols*BOX_W)/max(1,cols-1) if cols>1 else 0
    ROW_GAP = max(55, (AVAIL_H-rows*BOX_H)/max(1,rows-1)) if rows>1 else 0

    node_boxes: Dict[str, tuple] = {}
    for idx, e in enumerate(internal):
        r, col = idx//cols, idx%cols
        offset = 22 if rows>=3 and r%2==1 and cols>1 else 0
        x = INNER_LEFT + col*(BOX_W+COL_GAP) + offset
        y = INNER_TOP  + r*(BOX_H+ROW_GAP)
        x = min(x, SYS_X+SYS_W-65-BOX_W)
        c.rect(x, y, BOX_W, BOX_H, sw=2.2, rx=2)
        c.mtext(x+BOX_W/2, y+BOX_H/2, trunc(e.get("name",""),11), size=16, weight="bold", max_ch=8)
        ref = e.get("ref_no","")
        if ref: c.leader(x+BOX_W+52, y+8, x+BOX_W, y+BOX_H/2, ref)
        node_boxes[e.get("id","")] = (x, y, BOX_W, BOX_H)

    # 내부 연결 (기본 순차)
    for i in range(len(internal)-1):
        a = node_boxes.get(internal[i].get("id",""))
        b = node_boxes.get(internal[i+1].get("id",""))
        if not a or not b: continue
        ax,ay,aw,ah = a; bx,by,bw,bh = b
        if abs(ay-by) < 5:
            c.line(ax+aw, ay+ah/2, bx, by+bh/2, sw=1.8)
        else:
            c.polyline([(ax+aw/2, ay+ah),(ax+aw/2, by-26),(bx+bw/2, by-26),(bx+bw/2, by)], sw=1.8)

    # 외부→내부 연결
    if external and internal:
        fb = node_boxes.get(internal[0].get("id",""))
        if fb:
            fx,fy,fw,fh = fb
            for i, e in enumerate(external[:2]):
                eb = ext_boxes.get(e.get("id",""))
                if not eb: continue
                ex,ey,ew,eh = eb
                my = fy+fh/2+(i-0.5)*18
                c.polyline([(ex+ew, ey+eh/2),(SYS_X-24, ey+eh/2),(SYS_X-24, my),(fx, my)], sw=1.7)

    # 명시적 관계선 (최대 5개)
    drawn = 0
    for rel in relations:
        if drawn >= 5: break
        a = node_boxes.get(rel.get("from",""))
        b = node_boxes.get(rel.get("to",""))
        if not a or not b: continue
        ax,ay,aw,ah = a; bx,by,bw,bh = b
        if abs(ay-by) < 5: continue
        c.polyline([(ax+aw, ay+ah/2),(ax+aw+20, ay+ah/2),(ax+aw+20, by+bh/2),(bx, by+bh/2)],
                   sw=1.3, dash="4 2")
        lbl = rel.get("label","")
        if lbl: c.text(ax+aw+30, ay+ah/2-12, trunc(lbl,12), size=13, anchor="start", fill="#555")
        drawn += 1

    return c.to_svg(), {
        "layout_type": "patent_block_pro",
        "canvas": {"width": width, "height": height},
        "internal_count": len(internal), "external_count": len(external)
    }


# ─────────────────────────────────────────
# 렌더러 3: 시퀀스 다이어그램 (활성화 박스 포함)
# ─────────────────────────────────────────

def render_sequence(fig_json: dict) -> Tuple[str, dict]:
    elements = fig_json.get("elements", [])
    relations = fig_json.get("relations", [])

    actors = [e for e in elements if e.get("type") in ["actor","external","module"]]
    if not actors:
        actors = [{"id":"A0","name":"클라이언트"},{"id":"A1","name":"서버"}]

    ACT_W, ACT_H = 140, 58
    COL_GAP      = 185
    TOP          = 80
    MSG_GAP      = 68
    ACT_BOX_W    = 12  # 활성화 박스 너비

    n_actors = len(actors)
    n_msgs   = len(relations)
    width    = max(900, n_actors*(ACT_W+COL_GAP)+100)
    height   = TOP + ACT_H + n_msgs*MSG_GAP + 100

    c = SvgCanvas(width, height)
    fig_no = fig_json.get("fig_number","")
    title  = fig_json.get("title","")
    c.text(width/2, 36, f"{fig_no}  {title}", size=22, weight="bold")

    # 액터 위치
    total_w = n_actors*ACT_W + (n_actors-1)*COL_GAP
    start_x = (width-total_w)/2
    actor_cx: Dict[str, float] = {}
    for i, actor in enumerate(actors):
        ax = start_x + i*(ACT_W+COL_GAP)
        ay = TOP
        cx = ax + ACT_W/2
        actor_cx[actor["id"]] = cx
        # 상단 박스
        c.rect(ax, ay, ACT_W, ACT_H, sw=2.2, rx=3)
        c.mtext(cx, ay+ACT_H/2, trunc(actor.get("name",""),10), size=16, weight="bold", max_ch=8)
        # 생명선
        ll_top    = ay + ACT_H
        ll_bottom = height - 55
        c.line(cx, ll_top, cx, ll_bottom, sw=1.1, dash="6 4", arrow=False)
        # 하단 박스
        c.rect(ax, ll_bottom, ACT_W, ACT_H, sw=2.2, rx=3)
        c.mtext(cx, ll_bottom+ACT_H/2, trunc(actor.get("name",""),10), size=16, weight="bold", max_ch=8)

    # 활성화 박스 (생명선 위 얇은 사각형) - 메시지 구간
    msg_start_y = TOP + ACT_H + MSG_GAP

    # 활성화 구간 추적
    active_start: Dict[str, float] = {}
    active_boxes: List[Tuple[float,float,float,float]] = []  # (cx, top_y, bottom_y, w)

    for i, rel in enumerate(relations):
        fid  = rel.get("from","")
        tid  = rel.get("to","")
        fcx  = actor_cx.get(fid)
        tcx  = actor_cx.get(tid)
        if fcx is None or tcx is None: continue
        y    = msg_start_y + i*MSG_GAP
        mtype = rel.get("msg_type","sync")
        label = rel.get("label","")
        is_return = tcx < fcx

        # 자기 자신에게 (self-message)
        if fid == tid:
            lx = fcx + ACT_BOX_W/2
            c.path(f"M {lx:.1f},{y:.1f} L {lx+45:.1f},{y:.1f} L {lx+45:.1f},{y+30:.1f} L {lx:.1f},{y+30:.1f}",
                   sw=1.7, arrow=True)
            c.text(lx+48, y+15, trunc(label,16), size=13, anchor="start")
            continue

        dash = "5 3" if (is_return or mtype=="async") else None
        arrow_marker = "arr-open" if mtype=="async" else "arr"
        c.line(fcx, y, tcx, y, sw=1.7, dash=dash, arrow=True, marker=arrow_marker)

        # 레이블
        mid_x = (fcx+tcx)/2
        c.text(mid_x, y-13, trunc(label,20), size=13, anchor="middle")
        c.text(mid_x, y+13, str(i+1), size=12, anchor="middle", fill="#999")

        # 활성화 박스
        for cx in [fcx, tcx]:
            if cx not in active_start:
                active_start[cx] = y - 5
            active_boxes.append((cx, y-4, y+4, ACT_BOX_W))

    # 활성화 박스 그리기
    for (cx, ay2, by2, bw) in active_boxes:
        c.rect(cx-bw/2, ay2, bw, by2-ay2+10, sw=1.2, fill="#f0f0f0")

    return c.to_svg(), {
        "layout_type": "patent_sequence_pro",
        "canvas": {"width": width, "height": height},
        "actor_count": n_actors, "message_count": n_msgs
    }


# ─────────────────────────────────────────
# 렌더러 4: 상태 다이어그램 (둥근 사각형)
# ─────────────────────────────────────────

def render_state_diagram(fig_json: dict) -> Tuple[str, dict]:
    elements = fig_json.get("elements", [])
    relations = fig_json.get("relations", [])

    if not elements:
        elements = [
            {"id":"ST0","ref_no":"S0","name":"초기 상태"},
            {"id":"ST1","ref_no":"S1","name":"처리 중"},
            {"id":"ST2","ref_no":"S2","name":"완료"},
        ]

    n       = len(elements)
    NODE_W  = 160
    NODE_H  = 60
    width   = 1050
    height  = 820

    # 좌→우 또는 격자 배치 (자연스러운 흐름)
    c = SvgCanvas(width, height)
    fig_no = fig_json.get("fig_number","")
    title  = fig_json.get("title","")
    c.text(width/2, 40, f"{fig_no}  {title}", size=22, weight="bold")
    c.rect(48, 68, width-96, height-100, sw=1.5, dash="8 5")

    # 격자 배치
    cols = min(3, n)
    rows = math.ceil(n / cols)
    avail_w = width - 150
    avail_h = height - 200
    col_step = avail_w / max(cols, 1)
    row_step = avail_h / max(rows, 1)
    start_x = 75 + col_step/2
    start_y = 140

    positions: Dict[str, Tuple[float,float]] = {}
    for i, e in enumerate(elements):
        r, col = i//cols, i%cols
        px = start_x + col*col_step
        py = start_y + r*row_step
        positions[e["id"]] = (px, py)

    # 시작 마커 →첫 번째 상태
    if elements:
        fpx, fpy = positions[elements[0]["id"]]
        c.circle(fpx, fpy-NODE_H/2-35, 11, fill="#111")
        c.line(fpx, fpy-NODE_H/2-24, fpx, fpy-NODE_H/2, sw=2.0)

    # 상태 노드 (둥근 사각형)
    for i, e in enumerate(elements):
        eid = e["id"]
        px, py = positions[eid]
        name = trunc(e.get("name",""), 12)
        ref  = e.get("ref_no","")
        is_last = (i == len(elements)-1)

        if is_last and n > 1:
            # 종료 상태: 이중 둥근 사각형
            c.rect(px-NODE_W/2-5, py-NODE_H/2-5, NODE_W+10, NODE_H+10, sw=2.5, rx=26)
            c.rect(px-NODE_W/2, py-NODE_H/2, NODE_W, NODE_H, sw=2.0, rx=22, fill="#f8f8f8")
        else:
            c.rect(px-NODE_W/2, py-NODE_H/2, NODE_W, NODE_H, sw=2.2, rx=22)

        c.mtext(px, py, name, size=16, weight="bold", max_ch=8, gap=18)
        if ref: c.text(px+NODE_W/2+28, py-NODE_H/2+8, ref, size=15, weight="bold", anchor="start")

    # 종료 마커 ← 마지막 상태 아래
    if elements and n > 1:
        lpx, lpy = positions[elements[-1]["id"]]
        ey = lpy + NODE_H/2 + 38
        c.line(lpx, lpy+NODE_H/2, lpx, ey-14, sw=2.0)
        c.circle(lpx, ey, 13, fill="#fff", sw=3)
        c.circle(lpx, ey, 8, fill="#111")

    # 전이 화살표
    drawn_pairs: set = set()
    for rel in relations:
        fid = rel.get("from","")
        tid = rel.get("to","")
        fp  = positions.get(fid)
        tp  = positions.get(tid)
        if not fp or not tp: continue

        pair = (fid, tid)
        rev  = (tid, fid)
        is_rev = rev in drawn_pairs
        drawn_pairs.add(pair)

        fx, fy = fp; tx, ty = tp
        dx, dy = tx-fx, ty-fy
        dist = math.sqrt(dx*dx+dy*dy) or 1
        ux, uy = dx/dist, dy/dist
        sx = fx + ux*NODE_W/2
        sy = fy + uy*NODE_H/2
        ex2= tx - ux*NODE_W/2
        ey2= ty - uy*NODE_H/2

        label = rel.get("label","")

        if is_rev:
            # 역방향: 곡선
            off = 40
            px2 = -uy*off; py2 = ux*off
            mx = (sx+ex2)/2+px2; my = (sy+ey2)/2+py2
            c.path(f"M {sx:.1f},{sy:.1f} Q {mx:.1f},{my:.1f} {ex2:.1f},{ey2:.1f}",
                   sw=1.8, arrow=True)
            if label: c.text(mx, my-13, trunc(label,14), size=13, anchor="middle", fill="#333")
        else:
            c.line(sx, sy, ex2, ey2, sw=1.8)
            if label:
                lx = (sx+ex2)/2+(-uy*24); ly = (sy+ey2)/2+(ux*24)-8
                c.text(lx, ly, trunc(label,14), size=13, anchor="middle", fill="#333")

    return c.to_svg(), {
        "layout_type": "patent_state_pro",
        "canvas": {"width": width, "height": height},
        "state_count": n, "transition_count": len(relations)
    }


# ─────────────────────────────────────────
# 렌더러 5: UI 화면도
# ─────────────────────────────────────────

def render_ui_screen(fig_json: dict) -> Tuple[str, dict]:
    elements = fig_json.get("elements", [])
    if not elements:
        elements = [{"id":"UI100","ref_no":"100","name":"메인 화면","type":"module"}]

    width   = 960
    FRAME_X = 130
    FRAME_Y = 100
    FRAME_W = 700
    ELEM_H  = 65
    ELEM_GAP= 16
    frame_h = max(480, len(elements)*(ELEM_H+ELEM_GAP)+80)
    height  = frame_h + FRAME_Y + 90

    c = SvgCanvas(width, height)
    fig_no = fig_json.get("fig_number","")
    title  = fig_json.get("title","")
    c.text(width/2, 44, f"{fig_no}  {title}", size=22, weight="bold")

    # 디바이스 프레임 (둥근 사각형)
    c.rect(FRAME_X-22, FRAME_Y-32, FRAME_W+44, frame_h+64, sw=2.8, rx=16)
    # 상태바
    c.rect(FRAME_X-22, FRAME_Y-32, FRAME_W+44, 26, sw=0, fill="#e2e2e2", rx=6)
    c.circle(width/2-8, FRAME_Y-19, 4, fill="#aaa", sw=0)  # 카메라 홈
    c.text(width/2, FRAME_Y-19, "●", size=9, fill="#888")

    # 화면 내부 배경
    c.rect(FRAME_X, FRAME_Y, FRAME_W, frame_h, sw=1.0, fill="#fafafa")

    EX = FRAME_X + 18
    EW = FRAME_W - 36
    SY = FRAME_Y + 18

    for i, e in enumerate(elements):
        ey  = SY + i*(ELEM_H+ELEM_GAP)
        ref = e.get("ref_no","")
        name = trunc(e.get("name",""), 16)
        t   = str(e.get("type","module")).lower()

        if t in ["actor","container"] or i == 0:
            # 헤더 바
            c.rect(EX, ey, EW, ELEM_H, sw=1.5, fill="#e8e8e8", rx=4)
            c.line(EX, ey+ELEM_H, EX+EW, ey+ELEM_H, sw=2.0, arrow=False)
            c.text(EX+EW/2, ey+ELEM_H/2, name, size=17, weight="bold", anchor="middle")
        elif t in ["data","database"]:
            # 리스트/테이블 행
            c.rect(EX, ey, EW, ELEM_H, sw=1.3, dash="4 3", rx=2)
            c.line(EX+28, ey+8, EX+28, ey+ELEM_H-8, sw=1.0, arrow=False)
            c.text(EX+14, ey+ELEM_H/2, "≡", size=20, anchor="middle", fill="#888")
            c.text(EX+50, ey+ELEM_H/2, name, size=16, anchor="start")
        elif t == "process":
            # 버튼 (가운데 정렬)
            bw = min(260, EW*0.5)
            bx = EX + (EW-bw)/2
            c.rect(bx, ey+8, bw, ELEM_H-16, sw=2.0, rx=10, fill="#f0f0f0")
            c.text(EX+EW/2, ey+ELEM_H/2, name, size=16, weight="bold")
        else:
            # 입력 필드
            c.rect(EX, ey, EW, ELEM_H, sw=1.8, rx=5)
            c.text(EX+14, ey+ELEM_H/2, name, size=16, anchor="start", fill="#444")
            # 밑줄 힌트
            c.line(EX+10, ey+ELEM_H-10, EX+EW-10, ey+ELEM_H-10, sw=1.0, dash="3 2", arrow=False)

        # 도면부호 인출선 (오른쪽)
        if ref:
            c.leader(EX+EW+65, ey+14, EX+EW, ey+ELEM_H/2, ref)

    return c.to_svg(), {
        "layout_type": "patent_ui_pro",
        "canvas": {"width": width, "height": height},
        "element_count": len(elements)
    }


# ─────────────────────────────────────────
# 통합 렌더러
# ─────────────────────────────────────────

def render_patent_svg(fig_json: dict, style_template: str = DEFAULT_STYLE) -> Tuple[str, dict]:
    dtype = fig_json.get("diagram_type","block_diagram")
    if dtype in ["flowchart","method","process"]:
        return render_flowchart(fig_json)
    elif dtype == "sequence":
        return render_sequence(fig_json)
    elif dtype == "stateDiagram":
        return render_state_diagram(fig_json)
    elif dtype == "ui_screen":
        return render_ui_screen(fig_json)
    else:
        return render_block_diagram(fig_json)


# ─────────────────────────────────────────
# 검증 / 품질 점수
# ─────────────────────────────────────────

def validate_fig(fig: dict) -> dict:
    errors, warnings = [], []
    if not fig.get("fig_number"):  errors.append("fig_number 없음")
    if not fig.get("title"):       warnings.append("title 없음")
    elements = fig.get("elements",[])
    ids = {e.get("id") for e in elements if e.get("id")}
    if len(elements) < 2: warnings.append(f"구성요소 {len(elements)}개 (부족)")
    for e in elements:
        if not e.get("id"):   errors.append("id 없는 element")
        if not e.get("name"): warnings.append(f"{e.get('id')} name 없음")
    for r in fig.get("relations",[]):
        if r.get("from") not in ids: warnings.append(f"from 노드 없음: {r.get('from')}")
        if r.get("to")   not in ids: warnings.append(f"to 노드 없음: {r.get('to')}")
    return {"valid": not errors, "errors": errors, "warnings": warnings,
            "element_count": len(elements), "relation_count": len(fig.get("relations",[]))}

def score_quality(fig: dict, val: dict, layout: dict) -> dict:
    score, issues, strengths = 100, [], []
    elements = fig.get("elements",[])
    dtype    = fig.get("diagram_type","")
    PRO_LAYOUTS = ["patent_flow_pro","patent_block_pro","patent_sequence_pro",
                   "patent_state_pro","patent_ui_pro"]

    if len(elements) >= 3: strengths.append("구성요소 수 충분")
    else: score -= 15; issues.append("구성요소 3개 미만")

    no_ref = [e for e in elements if not e.get("ref_no")]
    if no_ref: score -= min(15, len(no_ref)*4); issues.append(f"도면부호 없는 요소 {len(no_ref)}개")
    else: strengths.append("도면부호 표시됨")

    if layout.get("layout_type") in PRO_LAYOUTS:
        strengths.append(f"특허청 실무 스타일 렌더링: {layout.get('layout_type')}")
    else:
        score -= 10; issues.append("프로 렌더링 메타데이터 없음")

    if not val.get("valid"):
        score -= 15; issues.extend(val.get("errors",[]))

    if dtype == "flowchart":
        n_dec = layout.get("decision_count", 0)
        if n_dec > 0: strengths.append(f"판단 마름모 {n_dec}개 포함")
        else: warnings_msg = "판단 단계 없음 (단순 순서도)"; issues.append(warnings_msg)

    ALLOWED = ["flowchart","block_diagram","sequence","ui_screen","stateDiagram","concept_diagram"]
    if dtype in ALLOWED: strengths.append("허용 도면 유형")
    else: score -= 10; issues.append(f"알 수 없는 유형: {dtype}")

    score = max(score, 0)
    grade = "A" if score>=90 else "B" if score>=75 else "C" if score>=60 else "D"
    return {"score": score, "grade": grade, "pass": score>=QUALITY_PASS_SCORE,
            "issues": issues, "strengths": strengths}

def make_validation_report(fig: dict, layout: dict) -> dict:
    val = validate_fig(fig)
    q   = score_quality(fig, val, layout)
    return {"valid": val["valid"], "quality": q, "fig_json_validation": val,
            "layout_meta": layout, "created_at": datetime.datetime.now().isoformat()}


# ─────────────────────────────────────────
# PNG 변환
# ─────────────────────────────────────────

def export_svg_to_png(svg_path: Path) -> str:
    png_path = str(svg_path).replace(".svg",".png")
    if CAIROSVG_AVAILABLE:
        try:
            cairosvg.svg2png(url=str(svg_path), write_to=png_path, dpi=220)
            return png_path
        except Exception as e:
            print(f"  [경고] cairosvg 실패: {e}")
    for cmd in [["magick", str(svg_path), png_path], ["convert", str(svg_path), png_path]]:
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return png_path
            except Exception:
                pass
    print("  [경고] PNG 변환기 없음. pip install cairosvg")
    return ""


# ─────────────────────────────────────────
# 자동 수정
# ─────────────────────────────────────────

REPAIR_PROMPT = """
특허 도면 설계 JSON을 개선하세요. JSON만 출력하세요.
- elements/relations 구조 유지
- 도면부호(ref_no) 없는 요소에 번호 추가
- 흐름도는 첫/마지막 요소 shape_type을 terminal로 설정
- 판단 단계는 shape_type을 decision으로, branches 추가
- SVG나 코드는 출력하지 말 것
"""

def repair_fig_json(fig: dict, val_result: dict, analysis: dict) -> dict:
    prompt = f"""
[현재 fig_json]
{json.dumps(fig, ensure_ascii=False, indent=2)}

[검증/품질 결과]
{json.dumps(val_result, ensure_ascii=False, indent=2)}

[특허 분석 참고]
{json.dumps(analysis, ensure_ascii=False, indent=2)[:8000]}
"""
    resp = client.chat.completions.create(
        model=MODEL_TEXT, max_tokens=4000, temperature=0.1,
        messages=[{"role":"system","content":REPAIR_PROMPT},
                  {"role":"user","content":prompt}]
    )
    return safe_json(resp.choices[0].message.content)


# ─────────────────────────────────────────
# Vision 검수
# ─────────────────────────────────────────

VISION_SYSTEM = """
특허 도면 분석 전문가입니다. 도면 이미지를 보고 JSON만 출력하세요.
{
  "recognized_components": [{"id":"100","name":"구성요소명","position":"상단","shape":"사각형"}],
  "connections": [{"from":"100","to":"200","label":"","arrow_type":"실선"}],
  "diagram_type": "flowchart|block_diagram|sequence|ui_screen|stateDiagram",
  "reference_numerals": ["100","200"],
  "missing_numerals": [],
  "issues_found": [{"severity":"warning","location":"","issue":"","suggestion":""}],
  "overall_quality": "excellent|good|fair|poor",
  "completeness_score": 85,
  "strengths": [],
  "summary": "도면 요약"
}
"""

def load_drawing_image(file_path: str) -> list:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일 없음: {file_path}")
    images = []
    ext = file_path.lower().rsplit(".",1)[-1]
    if ext == "pdf":
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError("pdf2image 필요: pip install pdf2image")
        pages = pdf2image.convert_from_path(file_path, dpi=150)
        for i, page in enumerate(pages):
            buf = io.BytesIO(); page.save(buf, format="PNG")
            images.append({"fig":f"도 {i+1}","base64":base64.b64encode(buf.getvalue()).decode(),
                           "media_type":"image/png","page":i+1})
    else:
        if PIL_AVAILABLE:
            img = Image.open(file_path)
            ms = 2048
            if max(img.size) > ms:
                r = ms/max(img.size)
                img = img.resize((int(img.width*r),int(img.height*r)), Image.LANCZOS)
            buf = io.BytesIO(); img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
        else:
            with open(file_path,"rb") as f: b64 = base64.b64encode(f.read()).decode()
        media_map = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","gif":"image/gif","webp":"image/webp"}
        images.append({"fig":"도 1","base64":b64,"media_type":media_map.get(ext,"image/png"),"page":1})
    print(f"  [4.01] 이미지 로드: {len(images)}페이지")
    return images

def analyze_image(img: dict, patent_text: str="") -> dict:
    content = [
        {"type":"image_url","image_url":{"url":f"data:{img['media_type']};base64,{img['base64']}","detail":"high"}},
        {"type":"text","text": VISION_SYSTEM + (f"\n\n[명세서 참고]\n{patent_text[:3000]}" if patent_text else "")}
    ]
    resp = client.chat.completions.create(
        model=MODEL_VISION, max_tokens=3000, temperature=0.1,
        messages=[{"role":"user","content":content}]
    )
    return safe_json(resp.choices[0].message.content)

def run_vision_review(png_path: str, patent_text: str="") -> dict:
    if not png_path or not os.path.exists(png_path):
        return {"enabled":False,"reason":"PNG 없음"}
    try:
        images = load_drawing_image(png_path)
        if not images: return {"enabled":False,"reason":"로드 실패"}
        r = analyze_image(images[0], patent_text)
        r["enabled"] = True; r["source_png"] = png_path
        return r
    except Exception as e:
        return {"enabled":False,"error":str(e)}


# ─────────────────────────────────────────
# 리포트
# ─────────────────────────────────────────

def save_report(app_dir: Path, app_num: str, results: list):
    scores = [r.quality_score for r in results]
    avg    = sum(scores)/len(scores) if scores else 0
    passed = sum(1 for r in results if r.quality_score >= QUALITY_PASS_SCORE)

    lines = [
        f"# 도면 생성 리포트 - {app_num}",
        f"- 생성일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 렌더러: 특허청 실무 SVG 렌더러 v7 (변리사/도면사 수준)",
        f"- 총 도면: {len(results)}, 평균 점수: {avg:.1f}, 통과: {passed}/{len(results)}",
        "",
        "## 지원 도면 유형",
        "| 유형 | 렌더러 | 특징 |",
        "|---|---|---|",
        "| flowchart | patent_flow_pro | 타원/마름모/사각형/평행사변형 + Yes/No 분기 |",
        "| block_diagram | patent_block_pro | 점선 시스템 경계 + 계층 구조 |",
        "| sequence | patent_sequence_pro | 활성화 박스 + 동기/비동기 화살표 |",
        "| stateDiagram | patent_state_pro | 둥근 사각형 + 초기/종료 마커 |",
        "| ui_screen | patent_ui_pro | 디바이스 프레임 + 타입별 UI 요소 |",
        "",
        "## 도면별 요약",
        "| 도면 | 제목 | 유형 | 점수 | 등급 | SVG |",
        "|---|---|---|---:|---|---|",
    ]
    for r in results:
        svg_name = Path(r.svg_path).name if r.svg_path else "-"
        lines.append(f"| {r.fig_number} | {r.diagram_title} | {r.diagram_type} | {r.quality_score} | {r.quality_grade} | {svg_name} |")

    with open(app_dir/"report.md","w",encoding="utf-8") as f:
        f.write("\n".join(lines))


# ─────────────────────────────────────────
# 메인 파이프라인
# ─────────────────────────────────────────

def generate_all_drawings(
    invention_text: str,
    app_num: str,
    output_dir: str = "drawing_analysis",
    export_svg: bool = True,
    export_png: bool = True,
    vision_review: bool = False,
    auto_repair: bool = True,
    max_repair_rounds: int = AUTO_REPAIR_ROUNDS,
    style_template: str = DEFAULT_STYLE,
) -> list:
    results = []
    app_dir = Path(output_dir)/app_num
    app_dir.mkdir(parents=True, exist_ok=True)

    local_figs = extract_figure_list(invention_text)
    local_refs = extract_refs(invention_text)
    save_json(app_dir/"local_extraction.json", {"figures":local_figs,"references":local_refs})

    print("  [3.10] 구성요소 추출 중...")
    analysis = extract_components(invention_text, app_num, local_figs, local_refs)
    analysis = merge_refs(analysis, local_refs)
    save_json(app_dir/"patent_analysis.json", analysis)
    print(f"  → 발명 유형: {analysis.get('invention_type')}")
    print(f"  → 핵심 개념: {analysis.get('main_concept')}")

    recommended = analysis.get("recommended_diagrams",[]) or local_figs or [
        {"fig_number":"도 1","diagram_type":"block_diagram","title":"전체 구성도","purpose":"전체 구성","source_text":"자동 생성"},
        {"fig_number":"도 2","diagram_type":"flowchart","title":"처리 흐름도","purpose":"처리 흐름","source_text":"자동 생성"},
    ]
    recommended = recommended[:2]
    save_json(app_dir/"figures.json", {"figures":recommended})

    for diagram_info in recommended:
        fig_num = diagram_info.get("fig_number","도 1")
        fig_id  = fig_num.replace(" ","_").replace("도","fig")

        print(f"  [3.11] {fig_num} '{diagram_info.get('title')}' 설계 중...")
        fig_json = build_fig_design(analysis, diagram_info)

        auto_repaired, repair_rounds = False, 0

        for attempt in range(max_repair_rounds+1):
            lbl = f" (수정 {attempt}회차)" if attempt else ""
            print(f"  [3.12] {fig_num} SVG 생성 중...{lbl}")
            svg_code, layout_meta = render_patent_svg(fig_json, style_template)
            val_result = make_validation_report(fig_json, layout_meta)
            quality    = val_result["quality"]

            if not auto_repair: break
            if quality["pass"] and val_result["valid"]: break
            if attempt >= max_repair_rounds: break

            print(f"  [3.12R] 품질 {quality['score']}점 → 자동 보정")
            try:
                fig_json = repair_fig_json(fig_json, val_result, analysis)
                auto_repaired = True; repair_rounds += 1
            except Exception as e:
                print(f"  [경고] 보정 실패: {e}"); break

        save_json(app_dir/f"{app_num}_{fig_id}.json", fig_json)
        save_json(app_dir/f"{app_num}_{fig_id}_layout.json", layout_meta)
        save_json(app_dir/f"{app_num}_{fig_id}_validation.json", val_result)

        svg_path = app_dir/f"{app_num}_{fig_id}.svg"
        png_path = ""

        if export_svg:
            print(f"  [3.13] SVG 저장...")
            with open(svg_path,"w",encoding="utf-8") as f: f.write(svg_code)
        else:
            svg_path = Path("")

        if export_png and svg_path:
            print(f"  [3.14] PNG 변환...")
            png_path = export_svg_to_png(svg_path)

        vision_path = ""
        if vision_review:
            print(f"  [4.03] Vision 검수...")
            vr = run_vision_review(png_path, invention_text)
            vp = app_dir/f"{app_num}_{fig_id}_vision.json"
            save_json(vp, vr); vision_path = str(vp)

        status = "통과" if quality["pass"] else "검토 필요"
        results.append(DrawingResult(
            app_num=app_num, fig_number=fig_num,
            diagram_type=fig_json.get("diagram_type",""),
            diagram_title=fig_json.get("title",""),
            quality_score=quality["score"], quality_grade=quality["grade"],
            fig_json_path=str(app_dir/f"{app_num}_{fig_id}.json"),
            svg_path=str(svg_path), png_path=png_path,
            layout_path=str(app_dir/f"{app_num}_{fig_id}_layout.json"),
            validation_path=str(app_dir/f"{app_num}_{fig_id}_validation.json"),
            vision_path=vision_path, style_template=style_template,
            auto_repaired=auto_repaired, repair_rounds=repair_rounds,
        ))
        print(f"  [저장] {svg_path} | 점수 {quality['score']}점 | {quality['grade']}등급 | {status}")

    save_json(app_dir/f"{app_num}_metadata.json", {
        "app_num": app_num, "created_at": datetime.datetime.now().isoformat(),
        "renderer": "patent_svg_pro_v7", "result_count": len(results),
        "results": [asdict(r) for r in results]
    })
    save_report(app_dir, app_num, results)
    return results


# ─────────────────────────────────────────
# 실행 유틸
# ─────────────────────────────────────────

def get_txt_files(limit=None):
    txt_files = []
    for d in PATENT_DIRS:
        found = glob.glob(f"{d}/*.txt")
        txt_files += found
        print(f"  {d}/: {len(found)}개")
    print(f"  합계: {len(txt_files)}개")
    if limit: txt_files = txt_files[:limit]; print(f"  처리 대상: {len(txt_files)}개")
    return txt_files

def run(limit=None, export_svg=True, export_png=True, vision_review=False,
        auto_repair=True, max_repair_rounds=AUTO_REPAIR_ROUNDS, style_template=DEFAULT_STYLE):
    print("="*60)
    print("도면 작성 Agent - 특허청 실무 SVG 렌더러 v7")
    print("="*60)
    txt_files = get_txt_files(limit)
    success = fail = skip = 0
    for i, f in enumerate(txt_files, 1):
        print(f"\n[{i}/{len(txt_files)}] {f}")
        try:
            parsed = parse_patent_txt(f)
            if not parsed["claims"] and not parsed["detail"]:
                print("  [스킵] 내용 없음"); skip += 1; continue
            results = generate_all_drawings(parsed["full"], parsed["app_num"], "drawing_analysis",
                export_svg=export_svg, export_png=export_png, vision_review=vision_review,
                auto_repair=auto_repair, max_repair_rounds=max_repair_rounds, style_template=style_template)
            if results:
                avg = sum(r.quality_score for r in results)/len(results)
                print(f"  ✅ {len(results)}개 도면 | 평균 {avg:.1f}점"); success += 1
            else: print("  [실패]"); fail += 1
        except KeyboardInterrupt: print("\n[중단]"); break
        except Exception as e: print(f"  [오류] {e}"); fail += 1
    print(f"\n{'='*60}\n배치 완료: 성공 {success} | 실패 {fail} | 스킵 {skip}\n{'='*60}")

def test_with_sample(**kwargs):
    sample = """
    본 발명은 딥러닝 기반 이미지 분류 시스템에 관한 것이다.
    사용자 단말기(10)는 이미지를 전송한다.
    이미지 분류 시스템(100)은 입력 이미지를 분석한다.
    입력부(110)는 이미지를 입력받는다.
    전처리부(120)는 이미지를 전처리한다. 이미지가 유효한지 여부를 판단한다.
    유효하지 않은 경우 오류를 반환한다.
    CNN 모델부(130)는 전처리된 이미지를 분류한다.
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
    results = generate_all_drawings(sample, "TEST-001", "drawing_analysis", **kwargs)
    print(f"\n✅ 생성된 도면: {len(results)}개")
    for r in results:
        print(f"  - {r.fig_number}: {r.quality_score}점/{r.quality_grade} | {r.svg_path}")

def test_with_real_file(**kwargs):
    txt_files = get_txt_files(limit=1)
    if not txt_files:
        print("[경고] txt 파일 없음 → 샘플 테스트")
        test_with_sample(**kwargs); return
    parsed = parse_patent_txt(txt_files[0])
    results = generate_all_drawings(parsed["full"], parsed["app_num"], "drawing_analysis", **kwargs)
    print(f"\n✅ 생성된 도면: {len(results)}개")
    for r in results:
        print(f"  - {r.fig_number}: {r.quality_score}점/{r.quality_grade} | {r.svg_path}")


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    HELP = """
사용법:
  python drawing_agent.py test
  python drawing_agent.py real
  python drawing_agent.py run 10
  python drawing_agent.py run 10 --vision
  python drawing_agent.py analyze <이미지> [<특허_txt>]

옵션:
  --vision         Vision 검수
  --no-svg         SVG 생성 끄기
  --no-png         PNG 생성 끄기
  --no-repair      자동 수정 끄기
  --repair-rounds N
"""
    args = sys.argv[1:]
    vision_review = "--vision" in args
    export_svg    = "--no-svg" not in args
    export_png    = "--no-png" not in args or vision_review
    auto_repair   = "--no-repair" not in args
    max_repair    = AUTO_REPAIR_ROUNDS

    if "--repair-rounds" in args:
        idx = args.index("--repair-rounds")
        if idx+1 < len(args): max_repair = int(args[idx+1])

    cleaned, skip_next = [], False
    for idx, a in enumerate(args):
        if skip_next: skip_next=False; continue
        if a in ["--vision","--no-svg","--no-png","--no-repair"]: continue
        if a in ["--repair-rounds"]: skip_next=True; continue
        cleaned.append(a)
    args = cleaned

    opts = dict(export_svg=export_svg, export_png=export_png, vision_review=vision_review,
                auto_repair=auto_repair, max_repair_rounds=max_repair)

    if not args or args[0] == "test":
        test_with_sample(**opts)
    elif args[0] == "real":
        test_with_real_file(**opts)
    elif args[0] == "run":
        limit = int(args[1]) if len(args)>1 else None
        run(limit, **opts)
    elif args[0] == "analyze":
        if len(args) < 2: print(HELP); sys.exit(1)
        imgs = load_drawing_image(args[1])
        patent_text = ""
        if len(args) > 2 and os.path.exists(args[2]):
            patent_text = parse_patent_txt(args[2])["full"]
        for img in imgs:
            result = analyze_image(img, patent_text)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(HELP)