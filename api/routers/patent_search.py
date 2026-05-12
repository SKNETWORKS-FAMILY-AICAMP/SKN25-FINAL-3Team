from fastapi import APIRouter
from api.schemas.patent import PatentSearchRequest, PatentSearchResponse
from agents.nodes import patent_search

router = APIRouter()


@router.post("", response_model=PatentSearchResponse)
async def search(request: PatentSearchRequest):
    result = patent_search.run(request.model_dump())
    return PatentSearchResponse(**result)
