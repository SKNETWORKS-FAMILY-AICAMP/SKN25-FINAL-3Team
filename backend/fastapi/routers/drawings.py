# backend/fastapi/routers/drawings.py
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
import logging
import boto3
from uuid import uuid4

from agents.summary_agent import SummaryAgent 
from agents.drawing_agent import SmartDrawingAgent 

logger = logging.getLogger(__name__)
router = APIRouter()

# S3 클라이언트 설정
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-2')
)
S3_BUCKET = os.getenv('S3_BUCKET')

@router.post("/generate-drawings")
async def generate_drawings_worker(request: Request):
    """도면 생성 워커"""
    data = await request.json()
    mock_input_data = data.get("mock_input_data")
    user_id = data.get("user_id", "unknown")
    project_id = data.get("project_id", "unknown")

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
            local_image_path = dwg.image_path
            
            # 그림 이름이 겹치지 않게 UUID 부착
            file_extension = os.path.splitext(local_image_path)[1] or ".png"
            unique_filename = f"drawing_{uuid4().hex[:8]}{file_extension}"
            
            # 유저와 프로젝트 ID 기반 동적 경로 생성
            s3_path = f"drawing-agent/uploads/user_{user_id}/project_{project_id}/{unique_filename}"
            
            # S3 업로드
            with open(local_image_path, "rb") as image_file:
                s3_client.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_path,
                    Body=image_file,
                    ContentType='image/png'
                )
            
            s3_url = f"https://{S3_BUCKET}.s3.{os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-2')}.amazonaws.com/{s3_path}"
            
            # 업로드 후 로컬 파일 삭제
            try:
                os.remove(local_image_path)
            except Exception as e:
                logger.warning(f"로컬 파일 지우기 실패: {e}")

            drawings_data.append({"title": dwg.title, "url": s3_url, "fig_no": dwg.fig_no})
        
        return {"status": "success", "drawings": drawings_data}

    except Exception as e:
        logger.error(f"도면 생성 워커 에러: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})