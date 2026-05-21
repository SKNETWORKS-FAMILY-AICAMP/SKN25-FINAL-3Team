# 개발/테스트용 경량 서버 — EXAONE 모델 없이 도면 에이전트만 실행
# uvicorn dev_server:app --host 0.0.0.0 --port 8000 --reload
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents.drawing.drawing_agent import generate_all_drawings

DRAWING_DIR = Path(__file__).resolve().parents[2] / "drawing_analysis"
DRAWING_DIR.mkdir(exist_ok=True)

app = FastAPI(title="PatentAI Dev Server")
app.mount("/drawing-files", StaticFiles(directory=str(DRAWING_DIR)), name="drawing_files")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ClaimRequest(BaseModel):
    consultation_note: str

class DrawingRequest(BaseModel):
    consultation_note: str

class FigureItem(BaseModel):
    fig_no: str
    title: str
    type: str
    svg_url: str | None = None

class ReferenceItem(BaseModel):
    number: str
    label: str


@app.get("/health")
def health():
    return {"status": "ok", "mode": "dev (no model)"}


@app.post("/generate-claims")
def generate_claims_mock(request: ClaimRequest):
    """개발용 mock — 실제 모델 없이 샘플 청구항 반환."""
    note = request.consultation_note[:100]
    return {
        "status": "success",
        "claim_1": f"[개발 mock] {note}...을 포함하는 시스템.",
        "dependent_claims": "제2항. 제1항에 있어서, AI 모델을 포함하는 시스템.\n제3항. 제1항에 있어서, 데이터 전처리부를 포함하는 시스템.",
    }


def _clean_patent_text(text: str) -> str:
    """특허 PDF에서 헤더를 제거하고 발명 설명 본문만 추출한다.

    pdfjs-dist는 【】를 그대로 추출하거나 공백을 삽입하기도 하므로
    다양한 패턴을 시도한다.
    """
    # 100자 이후에서 본문 시작 키워드 탐색
    search_start = 100
    markers = [
        "기술분야", "배경기술", "발명의 설명",
        "본 발명", "발명이 해결", "발명의 목적",
        "과제의 해결", "해결하고자",
    ]
    best_idx = None
    for marker in markers:
        idx = text.find(marker, search_start)
        if idx != -1 and (best_idx is None or idx < best_idx):
            best_idx = idx

    if best_idx is not None:
        # 본문만 최대 4000자
        return text[best_idx:best_idx + 4000].strip()

    # 마커 없으면 — (nn) 패턴 마지막 위치 이후 내용 사용
    matches = list(re.finditer(r'\(\d{1,3}\)', text[:800]))
    if matches:
        skip_to = matches[-1].end()
        return text[skip_to:skip_to + 4000].strip()

    # 최후 폴백: 앞 300자 스킵 후 4000자
    return text[300:4300].strip()


@app.post("/generate-drawings")
def generate_drawings(request: DrawingRequest):
    try:
        cleaned_text = _clean_patent_text(request.consultation_note)
        app_num = re.sub(r"[^A-Za-z0-9_-]", "_", "_".join(cleaned_text.split()[:6]))[:40] or "unknown"
        results = generate_all_drawings(cleaned_text, app_num, str(DRAWING_DIR))

        figures = []
        for r in results:
            nums = re.findall(r"\d+", r.fig_number)
            fig_no = nums[0] if nums else str(len(figures) + 1)
            svg_url = None
            if r.svg_path and Path(r.svg_path).exists():
                svg_url = f"/drawing-files/{app_num}/{Path(r.svg_path).name}"
            figures.append(FigureItem(fig_no=fig_no, title=r.diagram_title, type=r.diagram_type, svg_url=svg_url))

        ref_numerals = []
        analysis_path = DRAWING_DIR / app_num / "patent_analysis.json"
        if analysis_path.exists():
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            for comp in analysis.get("components", []):
                name = comp.get("name", "").strip()
                num  = str(comp.get("component_id") or comp.get("ref_no") or "")
                # 실제 구성요소만 — IPC코드·날짜·서술어·빈값 제외
                if not name or len(name) < 2 or len(name) > 15:
                    continue
                if re.search(r'G0[0-9][A-Z]|\d{4}년|있다$|이다$|됩니다|수 있|[()[\]/]', name):
                    continue
                ref_numerals.append(ReferenceItem(number=num or str(100 + len(ref_numerals) * 10), label=name))

        return {"status": "ok", "figures": [f.model_dump() for f in figures], "reference_numerals": [r.model_dump() for r in ref_numerals]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
