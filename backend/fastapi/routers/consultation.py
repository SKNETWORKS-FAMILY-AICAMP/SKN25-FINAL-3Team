from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ConsultStartRequest(BaseModel):
    user_id: str
    message: str


class ConsultReply(BaseModel):
    session_id: str
    response: str
    phase: int


@router.post("/start", response_model=ConsultReply)
async def start_consultation(req: ConsultStartRequest):
    """상담 세션 시작 — Phase 1 핵심요소 수집"""
    # TODO: PatentConsultant 연동
    raise HTTPException(status_code=501, detail="구현 예정")


@router.post("/{session_id}/message", response_model=ConsultReply)
async def send_message(session_id: str, req: ConsultStartRequest):
    """상담 메시지 전송"""
    # TODO: 세션 상태 조회 후 에이전트 호출
    raise HTTPException(status_code=501, detail="구현 예정")


@router.post("/{session_id}/finalize")
async def finalize_consultation(session_id: str):
    """상담 종료 및 DB 저장"""
    # TODO: consultation_agent.confirm_and_save()
    raise HTTPException(status_code=501, detail="구현 예정")
