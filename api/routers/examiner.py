from fastapi import APIRouter
from api.schemas.patent import ExaminerRequest, ExaminerResponse
from agents.nodes import examiner

router = APIRouter()


@router.post("", response_model=ExaminerResponse)
async def examine(request: ExaminerRequest):
    result = examiner.run(request.model_dump())
    return ExaminerResponse(**result)
