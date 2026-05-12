from fastapi import APIRouter
from api.schemas.patent import ClaimsRequest, ClaimsResponse
from agents.nodes import claims

router = APIRouter()


@router.post("", response_model=ClaimsResponse)
async def generate_claims(request: ClaimsRequest):
    result = claims.run(request.model_dump())
    return ClaimsResponse(**result)
