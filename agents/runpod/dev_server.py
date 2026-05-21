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


@app.post("/generate-drawings")
def generate_drawings(request: DrawingRequest):
    try:
        app_num = re.sub(r"[^A-Za-z0-9_-]", "_", "_".join(request.consultation_note.split()[:6]))[:40] or "unknown"
        results = generate_all_drawings(request.consultation_note, app_num, str(DRAWING_DIR))

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
            for i, comp in enumerate(analysis.get("components", [])):
                ref_numerals.append(ReferenceItem(number=str(100 + i * 10), label=comp.get("name", "")))

        return {"status": "ok", "figures": [f.model_dump() for f in figures], "reference_numerals": [r.model_dump() for r in ref_numerals]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
