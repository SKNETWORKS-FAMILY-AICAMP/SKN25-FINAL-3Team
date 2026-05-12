from fastapi import APIRouter
from api.schemas.patent import DescriptionRequest, DescriptionResponse
from agents.nodes import description

router = APIRouter()


@router.post("", response_model=DescriptionResponse)
async def generate_description(request: DescriptionRequest):
    result = description.run(request.model_dump())
    return DescriptionResponse(**result)
