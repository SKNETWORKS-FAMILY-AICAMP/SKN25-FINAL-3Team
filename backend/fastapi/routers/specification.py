# backend/fastapi/routers/specification.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

from agents.specification.specification_agent import run_specification_agent

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate-specification")
async def generate_specification_worker(request: Request):
    """명세서 생성 워커"""
    data = await request.json()
    agent_state = data.get("agent_state")

    try:
        result = run_specification_agent(agent_state)
        
        if result.get("status") != "ok":
            return JSONResponse(status_code=500, content={"message": str(result.get('warnings', ['알 수 없는 오류']))})
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"명세서 생성 워커 에러: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})