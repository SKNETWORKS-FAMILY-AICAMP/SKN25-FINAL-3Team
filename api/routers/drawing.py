from fastapi import APIRouter
from api.schemas.patent import DrawingRequest, DrawingResponse
from agents.nodes import drawing

router = APIRouter()


@router.post("", response_model=DrawingResponse)
async def generate_drawing(request: DrawingRequest):
    result = drawing.run(request.model_dump())
    return DrawingResponse(**result)
