import os
import logging
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


def _get_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2"),
    )


def upload_drawing(local_path: str, user_id: int, project_id: int) -> str:
    """
    로컬 도면 파일을 S3에 업로드하고 퍼블릭 URL을 반환.
    경로 포맷: uploads/user{user_id}/project{project_id}/{filename}
    """
    bucket = os.getenv("S3_BUCKET", "")
    if not bucket:
        raise ValueError("S3_BUCKET 환경변수가 설정되지 않았습니다.")

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"업로드할 파일이 없습니다: {local_path}")

    region   = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")
    filename = Path(local_path).name
    s3_key   = f"uploads/user{user_id}/project{project_id}/{filename}"

    try:
        client = _get_client()
        client.upload_file(
            local_path,
            bucket,
            s3_key,
            ExtraArgs={"ContentType": "image/png", "ACL": "public-read"},
        )
    except NoCredentialsError:
        raise NoCredentialsError("AWS 자격 증명을 찾을 수 없습니다.")
    except ClientError as e:
        logger.error(f"S3 업로드 실패 ({s3_key}): {e}")
        raise

    s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
    logger.info(f"S3 업로드 완료: {s3_url}")
    return s3_url


def delete_local(path: str) -> None:
    try:
        os.remove(path)
    except OSError as e:
        logger.warning(f"로컬 파일 삭제 실패 ({path}): {e}")
