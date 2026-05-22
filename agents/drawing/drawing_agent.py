# drawing_agent.py - 특허청 실무 도면 품질 SVG 렌더러 v7
import os, io, glob, json, re, math, shutil, datetime, subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict
from dotenv import load_dotenv
from openai import OpenAI

try: import base64; from PIL import Image; PIL_AVAILABLE = True
except ImportError: PIL_AVAILABLE = False
try: import pdf2image; PDF2IMAGE_AVAILABLE = True
except ImportError: PDF2IMAGE_AVAILABLE = False
try: import cairosvg; CAIROSVG_AVAILABLE = True
except Exception: CAIROSVG_AVAILABLE = False

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_TEXT, MODEL_VISION = "gpt-4o-mini", "gpt-4o"
PATENT_DIRS = ["G06F", "G06N", "G06Q", "G06V"]
QUALITY_PASS_SCORE, AUTO_REPAIR_ROUNDS, DEFAULT_STYLE = 75, 1, "patent_office"
MAX_BLOCK_ELEMENTS, MAX_FLOW_STEPS = 14, 14
FONT = "NanumGothic, Noto Sans CJK KR, Noto Sans KR, Malgun Gothic, Arial, sans-serif"


@dataclass
class DrawingResult:
    app_num: str; fig_number: str; diagram_type: str; diagram_title: str
    quality_score: int; quality_grade: str; fig_json_path: str; svg_path: str
    png_path: str = ""; layout_path: str = ""; validation_path: str = ""
    vision_path: str = ""; style_template: str = DEFAULT_STYLE
    auto_repaired: bool = False; repair_rounds: int = 0


# ── 공통 유틸 ──

def safe_json(raw: str) -> dict:
    raw = re.sub(r"```json\s*|\s*```", "", str(raw).strip()).strip()
    try: return json.loads(raw)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m: return json.loads(m.group())
    raise ValueError("JSON 파싱 실패")

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ns(text: str) -> str: return re.sub(r"\s+", " ", str(text or "")).strip()
def xe(s: str) -> str: return str(s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
def trunc(text: str, n: int = 20) -> str:
    text = ns(text); return text if len(text) <= n else text[:n-1] + "…"

def is_decision(name: str, step_type: str = "") -> bool:
    if step_type == "decision": return True
    return any(k in name for k in ["판단","확인","검사","여부","인지","확인하","결정","선택","검증","체크","비교"])

def is_terminal(name: str, step_type: str = "", idx: int = -1, total: int = 0) -> bool:
    if step_type == "terminal": return True
    if idx == 0 and any(k in name for k in ["시작","START","start","begin","Begin"]): return True
    if idx == total-1 and any(k in name for k in ["종료","END","end","완료","finish","Finish"]): return True
    return False


# ── 특허 파싱 ──

def extract_section(text, starts, ends):
    start = next((text.find(kw) for kw in starts if text.find(kw) != -1), -1)
    if start == -1: return ""
    ends_found = [text.find(kw, start+1) for kw in ends if text.find(kw, start+1) != -1]
    return text[start:(min(ends_found) if ends_found else start+6000)].strip()

def parse_patent_txt(txt_file: str) -> dict:
    with open(txt_file, "r", encoding="utf-8-sig") as f: text = f.read()
    app_num = os.path.basename(txt_file).replace(".txt","")
    claims,detail = extract_section(text,["청구범위"],["발명의 설명","요약","도면의 간단한 설명"]), extract_section(text,["발명의 설명","발명의 상세한 설명","상세한 설명"],["청구범위"])
    fig_desc,ref_desc = extract_section(text,["도면의 간단한 설명"],["발명을 실시하기 위한","발명의 효과","부호의 설명"]), extract_section(text,["부호의 설명"],["청구범위","요약","산업상"])
    return {"app_num":app_num,"claims":claims,"detail":detail,"figure_desc":fig_desc,"reference_desc":ref_desc,
            "full":f"[청구범위]\n{claims}\n\n[도면의 간단한 설명]\n{fig_desc}\n\n[부호의 설명]\n{ref_desc}\n\n[발명의 상세한 설명]\n{detail}".strip()}

def classify_type(title: str) -> str:
    t = title or ""
    if any(k in t for k in ["순서도","흐름도","플로우","과정","절차","방법","단계"]): return "flowchart"
    return "block_diagram"

def extract_figure_list(text: str) -> list:
    figs, seen = [], set()
    for pat in [r"도\s*(\d+[A-Za-z]?)\s*(?:은|는)\s*([^\n\.]+)",
                r"\[도\s*(\d+[A-Za-z]?)\]\s*([^\n]+)",
                r"도\s*(\d+[A-Za-z]?)\s*[:：]\s*([^\n]+)"]:
        for m in re.finditer(pat, text):
            fn = f"도 {m.group(1)}"
            if fn in seen: continue
            seen.add(fn); title = ns(m.group(2))
            figs.append({"fig_number": fn, "title": title, "diagram_type": classify_type(title),
                         "purpose": title, "source_text": m.group(0).strip()})
    figs.sort(key=lambda x: int(re.findall(r"\d+", x["fig_number"])[0]) if re.findall(r"\d+", x["fig_number"]) else 9999)
    return figs

def extract_refs(text: str) -> list:
    refs, seen = [], set()
    for pat in [r"(\d{2,5})\s*[:：]\s*([^\n,;]+)", r"(\d{2,5})\s*[\.]\s*([^\n,;]+)",
                r"(\d{2,5})\s*[-–]\s*([^\n,;]+)", r"([가-힣A-Za-z0-9\s]+)\((\d{2,5})\)"]:
        for m in re.finditer(pat, text):
            ref_no,name = (m.group(1).strip(),ns(m.group(2))) if m.group(1).isdigit() else (m.group(2).strip(),ns(m.group(1)))
            if ref_no in seen: continue
            seen.add(ref_no)
            refs.append({"ref_no":ref_no,"name":re.sub(r"(는|은|을|를|이|가)\s.*$","",name).strip()[:35],"source_text":m.group(0).strip()})
    return refs


# ── LLM 분석 ──

SYSTEM_PROMPT = """당신은 특허 명세서를 분석하여 도면 설계 JSON을 만드는 전문가입니다. JSON만 출력하세요.
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
규칙: 도면 2개 생성 / 흐름도: terminal→process→terminal / 구성요소 5개 이상 원문 그대로 / decision은 branches 필수"""

def extract_components(text: str, app_num: str, local_figs: list, local_refs: list) -> dict:
    prompt = f"특허 출원번호: {app_num}\n\n[도면 목록]\n{json.dumps(local_figs,ensure_ascii=False,indent=2)}\n\n[부호 설명]\n{json.dumps(local_refs,ensure_ascii=False,indent=2)}\n\n[특허 명세서]\n{text[:15000]}"
    resp = client.chat.completions.create(model=MODEL_TEXT, max_tokens=5000, temperature=0.1,
        messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])
    return safe_json(resp.choices[0].message.content)

def merge_refs(analysis: dict, local_refs: list) -> dict:
    comps=analysis.get("components",[]); existing={str(c.get("component_id","")).strip() for c in comps}
    for ref in local_refs:
        rn=str(ref.get("ref_no","")).strip()
        if rn and rn not in existing:
            comps.append({"component_id":rn,"name":ref.get("name",""),"component_type":"module","description":ref.get("name",""),"source_text":ref.get("source_text",""),"relationships":[]})
            existing.add(rn)
    analysis["components"]=comps; return analysis

def comp_priority(c: dict) -> int:
    n,t,i = str(c.get("name","")),str(c.get("component_type","")),str(c.get("component_id",""))
    return -(5*(t in ["container","device","external","actor"]) + 3*any(k in n for k in ["부","모듈","서버","단말","제어","처리","수신","전송","생성","저장"]) + 2*i.isdigit())


# ── fig_json 설계 ──

def build_fig_design(analysis: dict, diagram_info: dict) -> dict:
    dtype = diagram_info.get("diagram_type", "block_diagram")
    comps, flow, elements, relations = analysis.get("components",[]), analysis.get("process_flow",[]), [], []

    if dtype == "flowchart":
        n = len(flow)
        for idx, step in enumerate(flow[:MAX_FLOW_STEPS]):
            sid = step.get("step_id") or f"S{(idx+1)*100}"
            stype = step.get("step_type","process")
            if is_terminal(step.get("name",""), stype, idx, n): stype = "terminal"
            elif is_decision(step.get("name",""), stype): stype = "decision"
            elements.append({"id":sid,"ref_no":sid,"name":step.get("name","") or f"단계 {idx+1}",
                             "shape_type":stype,"description":step.get("description",""),
                             "source_text":step.get("source_text",""),"branches":step.get("branches",[])})
        relations = [{"from":elements[i]["id"],"to":elements[i+1]["id"],"label":""} for i in range(len(elements)-1)]

    else:  # block_diagram
        sorted_c = sorted(comps, key=comp_priority)[:MAX_BLOCK_ELEMENTS]
        for idx, c in enumerate(sorted_c, 1):
            cid = str(c.get("component_id","")).strip() or f"{idx*100}"
            nid = f"N{cid}" if cid and cid[0].isdigit() else (cid or f"N{idx}")
            elements.append({"id":nid,"ref_no":cid,"name":c.get("name",""),
                             "type":c.get("component_type","module"),"description":c.get("description",""),
                             "source_text":c.get("source_text","")})
        id_map = {str(e["ref_no"]): e["id"] for e in elements}
        for c in sorted_c:
            src = id_map.get(str(c.get("component_id","")).strip())
            if src:
                for rel in c.get("relationships",[]):
                    tgt = id_map.get(str(rel.get("target","")).strip())
                    if tgt: relations.append({"from":src,"to":tgt,"label":rel.get("label",""),"source_text":rel.get("source_text","")})

    return {"fig_number":diagram_info.get("fig_number","도 1"),"title":diagram_info.get("title",""),
            "diagram_type":dtype,"purpose":diagram_info.get("purpose",""),
            "figure_source_text":diagram_info.get("source_text",""),"elements":elements,"relations":relations}


# ── SVG 캔버스 ──

class SvgCanvas:
    def __init__(self, w: int, h: int):
        self.w, self.h, self.items = w, h, []
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

    def _da(self, dash): return f' stroke-dasharray="{dash}"' if dash else ""
    def _mk(self, arrow, marker): return f' marker-end="url(#{marker})"' if arrow else ""

    def rect(self, x,y,w,h, stroke="#111",fill="#fff",sw=2,dash=None,rx=0):
        self.items.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" ry="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{self._da(dash)}/>')

    def diamond(self, cx,cy,w,h, stroke="#111",fill="#fff",sw=2):
        pts = f"{cx:.1f},{cy-h/2:.1f} {cx+w/2:.1f},{cy:.1f} {cx:.1f},{cy+h/2:.1f} {cx-w/2:.1f},{cy:.1f}"
        self.items.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def oval(self, cx,cy,w,h, stroke="#111",fill="#fff",sw=2):
        self.items.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{w/2:.1f}" ry="{h/2:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def parallelogram(self, x,y,w,h, stroke="#111",fill="#fff",sw=2):
        sk=18; pts=f"{x+sk:.1f},{y:.1f} {x+w:.1f},{y:.1f} {x+w-sk:.1f},{y+h:.1f} {x:.1f},{y+h:.1f}"
        self.items.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def circle(self, cx,cy,r, stroke="#111",fill="#fff",sw=2):
        self.items.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def line(self, x1,y1,x2,y2, sw=1.7,dash=None,arrow=True,marker="arr"):
        self.items.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#111" stroke-width="{sw}" fill="none"{self._da(dash)}{self._mk(arrow,marker)}/>')

    def polyline(self, pts: List[Tuple[float,float]], sw=1.7,dash=None,arrow=True,marker="arr"):
        ps = " ".join(f"{x:.1f},{y:.1f}" for x,y in pts)
        self.items.append(f'<polyline points="{ps}" stroke="#111" stroke-width="{sw}" fill="none"{self._da(dash)}{self._mk(arrow,marker)}/>')

    def path(self, d:str, sw=1.7,dash=None,arrow=True,fill="none",marker="arr",stroke="#111"):
        self.items.append(f'<path d="{d}" stroke="{stroke}" fill="{fill}" stroke-width="{sw}"{self._da(dash)}{self._mk(arrow,marker)}/>')

    def text(self, x,y,t,size=17,weight="normal",anchor="middle",fill="#111"):
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" dominant-baseline="middle" fill="{fill}">{xe(t)}</text>')

    def mtext(self, x,y,t,size=15,weight="normal",anchor="middle",max_ch=9,gap=19):
        t=ns(t); chunks,cur=[],""
        for ch in t:
            cur+=ch
            if len(cur)>=max_ch: chunks.append(cur); cur=""
        chunks=chunks+([cur] if cur else []) or [""]
        for i,ln in enumerate(chunks[:3]):
            self.text(x,y-(len(chunks[:3])-1)*gap/2+i*gap,ln,size=size,weight=weight,anchor=anchor)

    def leader(self, tx,ty, lx,ly, ref:str, size=16):
        if not ref: return
        self.text(tx, ty, ref, size=size, weight="bold")
        self.line(tx, ty+size*0.6, lx, ly, sw=1.0, arrow=False)

    def to_svg(self) -> str:
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">\n'
                f'{self.defs}\n<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#ffffff"/>\n'
                f'{"".join(self.items)}\n</svg>')


# ── 렌더러 ──

def render_flowchart(fig_json: dict) -> Tuple[str, dict]:
    elements = fig_json.get("elements",[])[:MAX_FLOW_STEPS] or [
        {"id":"S100","ref_no":"S100","name":"시작","shape_type":"terminal","branches":[]},
        {"id":"S200","ref_no":"S200","name":"처리","shape_type":"process","branches":[]},
        {"id":"S300","ref_no":"S300","name":"종료","shape_type":"terminal","branches":[]},
    ]
    PW,PH,OW,OH,DW,DH,IW,IH,VG,MX = 340,72,280,60,320,90,320,65,48,480
    SIZES = {"terminal":(OW,OH),"decision":(DW,DH),"io":(IW,IH),"process":(PW,PH)}
    total_h = 110 + sum(SIZES.get(e.get("shape_type","process"),(PW,PH))[1]+VG for e in elements) + 80
    width, height = 960, max(900, total_h)
    c = SvgCanvas(width, height)
    c.text(width/2, 42, f"{fig_json.get('fig_number','')}  {fig_json.get('title','')}", size=22, weight="bold")
    c.rect(55, 72, width-110, height-100, sw=1.5, dash="8 5")
    box_info: Dict[str,dict] = {}; y = 110

    for e in elements:
        eid, st, name, ref, cx = e.get("id",""), e.get("shape_type","process"), trunc(e.get("name",""),14), e.get("ref_no",""), MX
        if st == "terminal":
            w,h = OW,OH; c.oval(cx, y+h/2, w, h, sw=2.4); c.mtext(cx, y+h/2, name, size=17, weight="bold", max_ch=10)
            if ref: c.leader(cx+w/2+55, y+10, cx+w/2, y+h/2, ref)
        elif st == "decision":
            w,h = DW,DH; c.diamond(cx, y+h/2, w, h, sw=2.2); c.mtext(cx, y+h/2, name, size=15, weight="bold", max_ch=9, gap=17)
            if ref: c.leader(cx+w/2+55, y+10, cx+w/2, y+h/2, ref)
        elif st == "io":
            w,h = IW,IH; c.parallelogram(cx-w/2, y, w, h, sw=2.0); c.mtext(cx, y+h/2, name, size=16, weight="bold", max_ch=11)
            if ref: c.leader(cx+w/2+55, y+8, cx+w/2, y+h/2, ref)
        else:
            w,h = PW,PH; c.rect(cx-w/2, y, w, h, sw=2.2); c.mtext(cx, y+h/2, name, size=17, weight="bold", max_ch=10)
            if ref: c.leader(cx+w/2+55, y+10, cx+w/2, y+h/2, ref)
        box_info[eid] = {"cx":cx,"cy":y+h/2,"top":y,"bottom":y+h,"w":w,"h":h}
        y += SIZES.get(st,(PW,PH))[1] + VG

    for i, e in enumerate(elements[:-1]):
        bi, bn = box_info.get(e.get("id","")), box_info.get(elements[i+1].get("id",""))
        if not bi or not bn: continue
        branches = e.get("branches",[])
        if e.get("shape_type") == "decision" and len(branches) >= 2:
            c.line(bi["cx"], bi["bottom"], bn["cx"], bn["top"], sw=1.8)
            c.text(bi["cx"]+14, (bi["bottom"]+bn["top"])/2, branches[0].get("label","예"), size=14, anchor="start", fill="#333")
            bx = bi["cx"] + DW/2
            c.polyline([(bx,bi["cy"]),(bx+80,bi["cy"]),(bx+80,bn["cy"]),(bn["cx"]+PW/2,bn["cy"])], sw=1.4, dash="5 3", arrow=False)
            c.text(bx+40, bi["cy"]-14, branches[1].get("label","아니오") if len(branches)>1 else "아니오", size=13, anchor="middle", fill="#666")
        else:
            c.line(bi["cx"], bi["bottom"], bn["cx"], bn["top"], sw=1.8)

    return c.to_svg(), {"layout_type":"patent_flow_pro","canvas":{"width":width,"height":height},
                        "step_count":len(elements),"decision_count":sum(1 for e in elements if e.get("shape_type")=="decision")}


def _is_external(e: dict) -> bool:
    return str(e.get("type","")) in ["actor","external"] or any(k in str(e.get("name","")) for k in ["사용자","단말","클라이언트","외부","관리자","네트워크","센서","카메라"])

def _is_container(e: dict) -> bool:
    if str(e.get("type","")) == "container": return True
    if _is_external(e): return False
    return any(k in str(e.get("name","")) for k in ["장치","시스템","플랫폼","서버","단말","모듈"])

def render_block_diagram(fig_json: dict) -> Tuple[str, dict]:
    elements, relations = fig_json.get("elements",[]), fig_json.get("relations",[])
    container = next((e for e in elements if _is_container(e)), None)
    rest = [e for e in elements if e is not container]
    external = [e for e in rest if _is_external(e)][:4]
    internal = [e for e in rest if not _is_external(e)][:12]
    if not internal and container: internal, container = [container], None
    n = max(1,len(internal)); cols = 3 if n>=5 else (2 if n>=3 else 1); rows = math.ceil(n/cols)
    width, height = 1200, max(780, 260+rows*155)
    EXT_W = 160 if external else 0
    SYS_X, SYS_Y = 110+EXT_W+(60 if external else 0), 105
    SYS_W, SYS_H = width-SYS_X-85, height-185
    c = SvgCanvas(width, height)
    c.text(width/2, 42, f"{fig_json.get('fig_number','')}  {fig_json.get('title','')}", size=22, weight="bold")
    c.rect(SYS_X, SYS_Y, SYS_W, SYS_H, sw=2.0, dash="10 5")
    cname = trunc(container.get("name","시스템") if container else "시스템", 16)
    cref  = container.get("ref_no","") if container else ""
    c.text(SYS_X+SYS_W/2, SYS_Y+26, cname, size=20, weight="bold")
    if cref: c.leader(SYS_X+SYS_W/2, SYS_Y-22, SYS_X+SYS_W/2, SYS_Y, cref)

    ext_boxes: Dict[str,tuple] = {}
    for i, e in enumerate(external):
        bx,by,bw,bh = 70,SYS_Y+90+i*155,EXT_W,85
        c.rect(bx,by,bw,bh,sw=2.2,rx=4); c.mtext(bx+bw/2,by+bh/2,trunc(e.get("name",""),10),size=16,weight="bold",max_ch=7)
        ref = e.get("ref_no","")
        if ref: c.leader(bx+bw+50,by+8,bx+bw,by+bh/2,ref)
        ext_boxes[e.get("id","")] = (bx,by,bw,bh)

    IL,IT = SYS_X+60, SYS_Y+85; AW,AH = SYS_W-120, SYS_H-130
    BOX_W = min(215, max(150,(AW-(cols-1)*55)/cols)); BOX_H = 75
    COL_GAP = (AW-cols*BOX_W)/max(1,cols-1) if cols>1 else 0
    ROW_GAP = max(55,(AH-rows*BOX_H)/max(1,rows-1)) if rows>1 else 0
    node_boxes: Dict[str,tuple] = {}
    for idx, e in enumerate(internal):
        r, col = idx//cols, idx%cols
        offset = 22 if rows>=3 and r%2==1 and cols>1 else 0
        x = min(IL+col*(BOX_W+COL_GAP)+offset, SYS_X+SYS_W-65-BOX_W); y = IT+r*(BOX_H+ROW_GAP)
        c.rect(x,y,BOX_W,BOX_H,sw=2.2,rx=2); c.mtext(x+BOX_W/2,y+BOX_H/2,trunc(e.get("name",""),11),size=16,weight="bold",max_ch=8)
        ref = e.get("ref_no","")
        if ref: c.leader(x+BOX_W+52,y+8,x+BOX_W,y+BOX_H/2,ref)
        node_boxes[e.get("id","")] = (x,y,BOX_W,BOX_H)

    for i in range(len(internal)-1):
        a,b = node_boxes.get(internal[i].get("id","")), node_boxes.get(internal[i+1].get("id",""))
        if not a or not b: continue
        ax,ay,aw,ah=a; bx,by,bw,bh=b
        if abs(ay-by)<5: c.line(ax+aw,ay+ah/2,bx,by+bh/2,sw=1.8)
        else: c.polyline([(ax+aw/2,ay+ah),(ax+aw/2,by-26),(bx+bw/2,by-26),(bx+bw/2,by)],sw=1.8)

    if external and internal:
        fb = node_boxes.get(internal[0].get("id",""))
        if fb:
            fx,fy,fw,fh=fb
            for i, e in enumerate(external[:2]):
                eb=ext_boxes.get(e.get("id",""))
                if not eb: continue
                ex,ey,ew,eh=eb; my=fy+fh/2+(i-0.5)*18
                c.polyline([(ex+ew,ey+eh/2),(SYS_X-24,ey+eh/2),(SYS_X-24,my),(fx,my)],sw=1.7)

    drawn = 0
    for rel in relations:
        if drawn>=5: break
        a,b = node_boxes.get(rel.get("from","")), node_boxes.get(rel.get("to",""))
        if not a or not b: continue
        ax,ay,aw,ah=a; bx,by,bw,bh=b
        if abs(ay-by)<5: continue
        c.polyline([(ax+aw,ay+ah/2),(ax+aw+20,ay+ah/2),(ax+aw+20,by+bh/2),(bx,by+bh/2)],sw=1.3,dash="4 2")
        lbl=rel.get("label","")
        if lbl: c.text(ax+aw+30,ay+ah/2-12,trunc(lbl,12),size=13,anchor="start",fill="#555")
        drawn+=1

    return c.to_svg(), {"layout_type":"patent_block_pro","canvas":{"width":width,"height":height},
                        "internal_count":len(internal),"external_count":len(external)}


def render_patent_svg(fig_json: dict, style_template: str = DEFAULT_STYLE) -> Tuple[str, dict]:
    dtype = fig_json.get("diagram_type","block_diagram")
    if dtype in ["flowchart","method","process"]: return render_flowchart(fig_json)
    return render_block_diagram(fig_json)


# ── 검증 / 품질 ──

def validate_fig(fig: dict) -> dict:
    elements=fig.get("elements",[]); ids={e.get("id") for e in elements if e.get("id")}
    errors  =(["fig_number 없음"] if not fig.get("fig_number") else [])+["id 없는 element" for e in elements if not e.get("id")]
    warnings=(["title 없음"] if not fig.get("title") else [])+\
             ([f"구성요소 {len(elements)}개 (부족)"] if len(elements)<2 else [])+\
             [f"{e.get('id')} name 없음" for e in elements if not e.get("name")]+\
             [f"from 노드 없음: {r.get('from')}" for r in fig.get("relations",[]) if r.get("from") not in ids]+\
             [f"to 노드 없음: {r.get('to')}" for r in fig.get("relations",[]) if r.get("to") not in ids]
    return {"valid":not errors,"errors":errors,"warnings":warnings,
            "element_count":len(elements),"relation_count":len(fig.get("relations",[]))}

def score_quality(fig: dict, val: dict, layout: dict) -> dict:
    score,issues,strengths = 100,[],[]
    elements=fig.get("elements",[]); dtype=fig.get("diagram_type","")
    PRO={"patent_flow_pro","patent_block_pro"}
    VALID={"flowchart","block_diagram"}
    no_ref=[e for e in elements if not e.get("ref_no")]
    if len(elements)>=3: strengths.append("구성요소 수 충분")
    else: score-=15; issues.append("구성요소 3개 미만")
    if no_ref: score-=min(15,len(no_ref)*4); issues.append(f"도면부호 없는 요소 {len(no_ref)}개")
    else: strengths.append("도면부호 표시됨")
    if layout.get("layout_type") in PRO: strengths.append(f"특허청 실무 스타일: {layout.get('layout_type')}")
    else: score-=10; issues.append("프로 렌더링 메타데이터 없음")
    if not val.get("valid"): score-=15; issues.extend(val.get("errors",[]))
    if dtype=="flowchart":
        n=layout.get("decision_count",0)
        (strengths if n else issues).append(f"판단 마름모 {n}개 포함" if n else "판단 단계 없음 (단순 순서도)")
    if dtype in VALID: strengths.append("허용 도면 유형")
    else: score-=10; issues.append(f"알 수 없는 유형: {dtype}")
    score=max(score,0); grade="A" if score>=90 else "B" if score>=75 else "C" if score>=60 else "D"
    return {"score":score,"grade":grade,"pass":score>=QUALITY_PASS_SCORE,"issues":issues,"strengths":strengths}

def make_validation_report(fig: dict, layout: dict) -> dict:
    val=validate_fig(fig); q=score_quality(fig,val,layout)
    return {"valid":val["valid"],"quality":q,"fig_json_validation":val,"layout_meta":layout,"created_at":datetime.datetime.now().isoformat()}


# ── PNG 변환 ──

def export_svg_to_png(svg_path: Path) -> str:
    png_path = str(svg_path).replace(".svg",".png")
    if CAIROSVG_AVAILABLE:
        try: cairosvg.svg2png(url=str(svg_path), write_to=png_path, dpi=220); return png_path
        except Exception as e: print(f"  [경고] cairosvg 실패: {e}")
    for cmd in [["magick",str(svg_path),png_path],["convert",str(svg_path),png_path]]:
        if shutil.which(cmd[0]):
            try: subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE); return png_path
            except Exception: pass
    print("  [경고] PNG 변환기 없음. pip install cairosvg"); return ""


# ── 자동 수정 ──

REPAIR_PROMPT = """특허 도면 설계 JSON을 개선하세요. JSON만 출력하세요.
- 도면부호(ref_no) 없는 요소에 번호 추가
- 흐름도 첫/마지막 요소 shape_type=terminal, 판단 단계 shape_type=decision + branches 추가"""

def repair_fig_json(fig: dict, val_result: dict, analysis: dict) -> dict:
    prompt = f"[현재 fig_json]\n{json.dumps(fig,ensure_ascii=False,indent=2)}\n\n[검증/품질 결과]\n{json.dumps(val_result,ensure_ascii=False,indent=2)}\n\n[특허 분석 참고]\n{json.dumps(analysis,ensure_ascii=False,indent=2)[:8000]}"
    resp = client.chat.completions.create(model=MODEL_TEXT, max_tokens=4000, temperature=0.1,
        messages=[{"role":"system","content":REPAIR_PROMPT},{"role":"user","content":prompt}])
    return safe_json(resp.choices[0].message.content)


# ── Vision 검수 ──

VISION_SYSTEM = """특허 도면 분석 전문가입니다. 도면 이미지를 보고 JSON만 출력하세요.
{"recognized_components":[{"id":"100","name":"","position":"","shape":""}],"connections":[{"from":"100","to":"200","label":"","arrow_type":"실선"}],"diagram_type":"","reference_numerals":[],"missing_numerals":[],"issues_found":[{"severity":"warning","location":"","issue":"","suggestion":""}],"overall_quality":"excellent|good|fair|poor","completeness_score":85,"strengths":[],"summary":""}"""

def load_drawing_image(file_path: str) -> list:
    if not os.path.exists(file_path): raise FileNotFoundError(f"파일 없음: {file_path}")
    images = []; ext = file_path.lower().rsplit(".",1)[-1]
    if ext == "pdf":
        if not PDF2IMAGE_AVAILABLE: raise ImportError("pdf2image 필요: pip install pdf2image")
        for i, page in enumerate(pdf2image.convert_from_path(file_path, dpi=150)):
            buf=io.BytesIO(); page.save(buf,format="PNG")
            images.append({"fig":f"도 {i+1}","base64":base64.b64encode(buf.getvalue()).decode(),"media_type":"image/png","page":i+1})
    else:
        if PIL_AVAILABLE:
            img=Image.open(file_path); ms=2048
            if max(img.size)>ms: r=ms/max(img.size); img=img.resize((int(img.width*r),int(img.height*r)),Image.LANCZOS)
            buf=io.BytesIO(); img.save(buf,format="PNG"); b64=base64.b64encode(buf.getvalue()).decode()
        else:
            with open(file_path,"rb") as f: b64=base64.b64encode(f.read()).decode()
        media_map={"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","gif":"image/gif","webp":"image/webp"}
        images.append({"fig":"도 1","base64":b64,"media_type":media_map.get(ext,"image/png"),"page":1})
    print(f"  [4.01] 이미지 로드: {len(images)}페이지"); return images

def analyze_image(img: dict, patent_text: str="") -> dict:
    content=[{"type":"image_url","image_url":{"url":f"data:{img['media_type']};base64,{img['base64']}","detail":"high"}},
             {"type":"text","text":VISION_SYSTEM+(f"\n\n[명세서 참고]\n{patent_text[:3000]}" if patent_text else "")}]
    resp=client.chat.completions.create(model=MODEL_VISION,max_tokens=3000,temperature=0.1,
        messages=[{"role":"user","content":content}])
    return safe_json(resp.choices[0].message.content)

def run_vision_review(png_path: str, patent_text: str="") -> dict:
    if not png_path or not os.path.exists(png_path): return {"enabled":False,"reason":"PNG 없음"}
    try:
        images=load_drawing_image(png_path)
        if not images: return {"enabled":False,"reason":"로드 실패"}
        r=analyze_image(images[0],patent_text); r["enabled"]=True; r["source_png"]=png_path; return r
    except Exception as e: return {"enabled":False,"error":str(e)}


# ── 리포트 ──

def save_report(app_dir: Path, app_num: str, results: list):
    avg=sum(r.quality_score for r in results)/len(results) if results else 0
    passed=sum(1 for r in results if r.quality_score>=QUALITY_PASS_SCORE)
    hdr=[f"# 도면 생성 리포트 - {app_num}",
         f"- {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 렌더러: 특허청 실무 SVG 렌더러 v7",
         f"- 총 도면: {len(results)}, 평균 점수: {avg:.1f}, 통과: {passed}/{len(results)}","",
         "| 도면 | 제목 | 유형 | 점수 | 등급 | SVG |","|---|---|---|---:|---|---|"]
    rows=[f"| {r.fig_number} | {r.diagram_title} | {r.diagram_type} | {r.quality_score} | {r.quality_grade} | {Path(r.svg_path).name if r.svg_path else '-'} |" for r in results]
    with open(app_dir/"report.md","w",encoding="utf-8") as f: f.write("\n".join(hdr+rows))


# ── 메인 파이프라인 ──

def generate_all_drawings(invention_text: str, app_num: str, output_dir: str = "drawing_analysis",
    export_svg=True, export_png=True, vision_review=False, auto_repair=True,
    max_repair_rounds=AUTO_REPAIR_ROUNDS, style_template=DEFAULT_STYLE) -> list:
    results = []; app_dir = Path(output_dir)/app_num; app_dir.mkdir(parents=True, exist_ok=True)
    local_figs = extract_figure_list(invention_text); local_refs = extract_refs(invention_text)
    save_json(app_dir/"local_extraction.json", {"figures":local_figs,"references":local_refs})
    print("  [3.10] 구성요소 추출 중...")
    analysis = merge_refs(extract_components(invention_text, app_num, local_figs, local_refs), local_refs)
    save_json(app_dir/"patent_analysis.json", analysis)
    print(f"  → 발명 유형: {analysis.get('invention_type')} / 핵심 개념: {analysis.get('main_concept')}")
    recommended = analysis.get("recommended_diagrams", []) or local_figs or [
        {"fig_number":"도 1","diagram_type":"block_diagram","title":"전체 구성도","purpose":"전체 구성","source_text":"자동 생성"},
        {"fig_number":"도 2","diagram_type":"flowchart","title":"처리 흐름도","purpose":"처리 흐름","source_text":"자동 생성"},
    ]

    # block_diagram, flowchart 2종만 생성
    recommended = [d for d in recommended if d.get("diagram_type") in {"block_diagram","flowchart"}]
    if not any(d.get("diagram_type")=="block_diagram" for d in recommended):
        recommended.insert(0, {"fig_number":"도 1","diagram_type":"block_diagram","title":"전체 구성도","purpose":"전체 구성","source_text":"자동 생성"})
    if not any(d.get("diagram_type")=="flowchart" for d in recommended):
        n = len(recommended) + 1
        recommended.append({"fig_number":f"도 {n}","diagram_type":"flowchart","title":"처리 흐름도","purpose":"처리 흐름","source_text":"자동 생성"})

    save_json(app_dir/"figures.json", {"figures":recommended})

    for diagram_info in recommended:
        fig_num = diagram_info.get("fig_number","도 1")
        fig_id  = fig_num.replace(" ","_").replace("도","fig")
        print(f"  [3.11] {fig_num} '{diagram_info.get('title')}' 설계 중...")
        fig_json = build_fig_design(analysis, diagram_info)
        auto_repaired, repair_rounds = False, 0

        for attempt in range(max_repair_rounds+1):
            svg_code, layout_meta = render_patent_svg(fig_json, style_template)
            val_result = make_validation_report(fig_json, layout_meta)
            quality = val_result["quality"]
            if not auto_repair or (quality["pass"] and val_result["valid"]) or attempt >= max_repair_rounds: break
            print(f"  [3.12R] 품질 {quality['score']}점 → 자동 보정")
            try: fig_json=repair_fig_json(fig_json,val_result,analysis); auto_repaired=True; repair_rounds+=1
            except Exception as e: print(f"  [경고] 보정 실패: {e}"); break

        save_json(app_dir/f"{app_num}_{fig_id}.json", fig_json)
        save_json(app_dir/f"{app_num}_{fig_id}_layout.json", layout_meta)
        save_json(app_dir/f"{app_num}_{fig_id}_validation.json", val_result)
        svg_path = app_dir/f"{app_num}_{fig_id}.svg"
        if export_svg:
            with open(svg_path,"w",encoding="utf-8") as f: f.write(svg_code)
        else: svg_path = Path("")
        png_path = export_svg_to_png(svg_path) if export_png and svg_path else ""
        vision_path = ""
        if vision_review:
            vr=run_vision_review(png_path,invention_text); vp=app_dir/f"{app_num}_{fig_id}_vision.json"
            save_json(vp,vr); vision_path=str(vp)
        results.append(DrawingResult(
            app_num=app_num, fig_number=fig_num, diagram_type=fig_json.get("diagram_type",""),
            diagram_title=fig_json.get("title",""), quality_score=quality["score"], quality_grade=quality["grade"],
            fig_json_path=str(app_dir/f"{app_num}_{fig_id}.json"), svg_path=str(svg_path), png_path=png_path,
            layout_path=str(app_dir/f"{app_num}_{fig_id}_layout.json"),
            validation_path=str(app_dir/f"{app_num}_{fig_id}_validation.json"),
            vision_path=vision_path, style_template=style_template,
            auto_repaired=auto_repaired, repair_rounds=repair_rounds))
        print(f"  [저장] {svg_path} | {quality['score']}점 | {quality['grade']}등급")

    save_json(app_dir/f"{app_num}_metadata.json", {"app_num":app_num,"created_at":datetime.datetime.now().isoformat(),
        "renderer":"patent_svg_pro_v7","result_count":len(results),"results":[asdict(r) for r in results]})
    save_report(app_dir, app_num, results); return results


def get_txt_files(limit=None):
    txt_files=sum([glob.glob(f"{d}/*.txt") for d in PATENT_DIRS],[])
    for d in PATENT_DIRS: print(f"  {d}/: {len(glob.glob(f'{d}/*.txt'))}개")
    print(f"  합계: {len(txt_files)}개")
    if limit: txt_files=txt_files[:limit]; print(f"  처리 대상: {limit}개")
    return txt_files

def run(limit=None, export_svg=True, export_png=True, vision_review=False,
        auto_repair=True, max_repair_rounds=AUTO_REPAIR_ROUNDS, style_template=DEFAULT_STYLE):
    print("="*60+"\n도면 작성 Agent - 특허청 실무 SVG 렌더러 v7\n"+"="*60)
    txt_files=get_txt_files(limit); success=fail=skip=0
    for i, f in enumerate(txt_files, 1):
        print(f"\n[{i}/{len(txt_files)}] {f}")
        try:
            parsed=parse_patent_txt(f)
            if not parsed["claims"] and not parsed["detail"]: print("  [스킵] 내용 없음"); skip+=1; continue
            results=generate_all_drawings(parsed["full"],parsed["app_num"],"drawing_analysis",
                export_svg=export_svg,export_png=export_png,vision_review=vision_review,
                auto_repair=auto_repair,max_repair_rounds=max_repair_rounds,style_template=style_template)
            if results: avg=sum(r.quality_score for r in results)/len(results); print(f"  ✅ {len(results)}개 도면 | 평균 {avg:.1f}점"); success+=1
            else: print("  [실패]"); fail+=1
        except KeyboardInterrupt: print("\n[중단]"); break
        except Exception as e: print(f"  [오류] {e}"); fail+=1
    print(f"\n{'='*60}\n배치 완료: 성공 {success} | 실패 {fail} | 스킵 {skip}\n{'='*60}")

def test_with_sample(**kwargs):
    sample = """본 발명은 딥러닝 기반 이미지 분류 시스템에 관한 것이다.
사용자 단말기(10)는 이미지를 전송한다. 이미지 분류 시스템(100)은 입력 이미지를 분석한다.
입력부(110)는 이미지를 입력받는다. 전처리부(120)는 이미지를 전처리한다. 이미지가 유효한지 여부를 판단한다.
유효하지 않은 경우 오류를 반환한다. CNN 모델부(130)는 전처리된 이미지를 분류한다.
저장부(140)는 분석 결과를 저장한다. 출력부(150)는 분류 결과를 출력한다.
도 1은 이미지 분류 시스템의 전체 구성도이다. 도 2는 이미지 분류 방법의 처리 흐름도이다.
부호의 설명
10: 사용자 단말기  100: 이미지 분류 시스템  110: 입력부
120: 전처리부  130: CNN 모델부  140: 저장부  150: 출력부"""
    results=generate_all_drawings(sample,"TEST-001","drawing_analysis",**kwargs)
    print(f"\n✅ 생성된 도면: {len(results)}개")
    for r in results: print(f"  - {r.fig_number}: {r.quality_score}점/{r.quality_grade} | {r.svg_path}")

def test_with_real_file(**kwargs):
    txt_files=get_txt_files(limit=1)
    if not txt_files: print("[경고] txt 파일 없음 → 샘플 테스트"); test_with_sample(**kwargs); return
    parsed=parse_patent_txt(txt_files[0])
    results=generate_all_drawings(parsed["full"],parsed["app_num"],"drawing_analysis",**kwargs)
    print(f"\n✅ 생성된 도면: {len(results)}개")
    for r in results: print(f"  - {r.fig_number}: {r.quality_score}점/{r.quality_grade} | {r.svg_path}")


# ── CLI ──

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    vision_review = "--vision" in args; export_svg = "--no-svg" not in args
    export_png = "--no-png" not in args or vision_review; auto_repair = "--no-repair" not in args
    max_repair = int(args[args.index("--repair-rounds")+1]) if "--repair-rounds" in args else AUTO_REPAIR_ROUNDS
    FLAGS = {"--vision","--no-svg","--no-png","--no-repair","--repair-rounds"}
    cleaned, skip_next = [], False
    for a in args:
        if skip_next: skip_next=False; continue
        if a in FLAGS: skip_next=(a=="--repair-rounds"); continue
        cleaned.append(a)
    args = cleaned
    opts = dict(export_svg=export_svg,export_png=export_png,vision_review=vision_review,
                auto_repair=auto_repair,max_repair_rounds=max_repair)
    if not args or args[0]=="test": test_with_sample(**opts)
    elif args[0]=="real": test_with_real_file(**opts)
    elif args[0]=="run": run(int(args[1]) if len(args)>1 else None,**opts)
    elif args[0]=="analyze":
        if len(args)<2: print("사용법: python drawing_agent.py analyze <이미지> [<특허_txt>]"); sys.exit(1)
        imgs=load_drawing_image(args[1]); patent_text=""
        if len(args)>2 and os.path.exists(args[2]): patent_text=parse_patent_txt(args[2])["full"]
        for img in imgs: print(json.dumps(analyze_image(img,patent_text),ensure_ascii=False,indent=2))
