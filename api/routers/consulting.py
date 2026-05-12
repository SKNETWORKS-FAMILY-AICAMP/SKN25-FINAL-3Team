from fastapi import APIRouter
from api.schemas.patent import ConsultRequest, ConsultResponse
from agents.nodes import consulting

router = APIRouter()


@router.post("", response_model=ConsultResponse)
async def consult(request: ConsultRequest):
    state = {
        "user_input": request.user_input,
        "user_id": request.user_id,
        "session_id": request.session_id,
    }
    result = consulting.run(state)
    return ConsultResponse(**result)
