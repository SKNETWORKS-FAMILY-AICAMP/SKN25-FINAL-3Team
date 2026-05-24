from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class PipelineRunRequest(BaseModel):
    user_id: str
    consultation_idx: int


class PipelineStatus(BaseModel):
    job_id: str
    stage: str           # summary | claim | drawing | prior_art | specification | composer | done
    status: str          # running | ok | failed
    current_agent: str | None = None
    result_preview: str | None = None


@router.post("/run", response_model=PipelineStatus)
async def run_pipeline(req: PipelineRunRequest):
    """멀티에이전트 파이프라인 실행
    DEFAULT_PIPELINE: summary → claim → drawing → prior_art → specification → composer
    """
    # TODO: agents.graph.run_pipeline() 연동
    raise HTTPException(status_code=501, detail="구현 예정")


@router.get("/{job_id}/status", response_model=PipelineStatus)
async def get_pipeline_status(job_id: str):
    """파이프라인 실행 상태 조회"""
    # TODO: 상태 저장소(Redis 또는 DB) 조회
    raise HTTPException(status_code=501, detail="구현 예정")


@router.get("/{job_id}/result")
async def get_pipeline_result(job_id: str):
    """파이프라인 최종 결과(ComposerAgentOutput) 조회"""
    # TODO: state["final_package"] 반환
    raise HTTPException(status_code=501, detail="구현 예정")
