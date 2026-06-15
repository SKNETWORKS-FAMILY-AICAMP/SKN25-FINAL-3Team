# backend/fastapi/routers/drawings.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
import logging

from agents.summary_agent import SummaryAgent 
from agents.drawing_agent import SmartDrawingAgent 

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate-drawings")
async def generate_drawings_worker(request: Request):
    """도면 생성 워커"""
    data = await request.json()
    mock_input_data = data.get("mock_input_data")

    try:
        summary_agent = SummaryAgent(model_name="gpt-4o-mini")
        summary_state = summary_agent.run({"mock_input_data": mock_input_data})
        
        drawing_agent = SmartDrawingAgent()
        drawing_result = drawing_agent.run(summary_state)
        
        drawing_spec = drawing_result.get("drawing_spec")
        if not drawing_spec:
            return JSONResponse(status_code=500, content={"message": "도면 생성에 실패했습니다."})

        drawings_data = []
        for dwg in drawing_spec.drawings:
            file_name = os.path.basename(dwg.image_path)
            drawings_data.append({"title": dwg.title, "file_name": file_name, "fig_no": dwg.fig_no})
        
        return {"status": "success", "drawings": drawings_data}

    except Exception as e:
        logger.error(f"도면 생성 워커 에러: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})