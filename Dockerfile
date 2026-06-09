# 1. 베이스 이미지 설정 (Python 3.12)
FROM python:3.12-slim

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# 3. 최신 uv 설치 (공식 권장 방식)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. 의존성 파일 복사 및 설치 (캐시 최적화를 위해 먼저 복사)
COPY pyproject.toml uv.lock ./
# --frozen: uv.lock 파일을 기준으로 설치하며, lock 파일이 변경되지 않도록 보장
RUN uv sync --frozen --no-dev

# 6. 프로젝트 전체 코드 복사
COPY . .

# 7. 포트 노출 (Django 기본 포트)
EXPOSE 8000

# 8. 컨테이너 실행 시 Django 서버 가동 (필요에 따라 fastapi uvicorn으로 변경 가능)
CMD ["uv", "run", "python", "backend/manage.py", "runserver", "0.0.0.0:8000"]