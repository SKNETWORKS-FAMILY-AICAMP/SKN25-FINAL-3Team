# 1. 베이스 이미지 설정 (Python 3.12)
FROM python:3.12-slim

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/backend" \
    # 핵심 1: 가상환경을 /app 폴더 밖인 /venv 에 만들도록 지시
    UV_PROJECT_ENVIRONMENT=/venv \
    # 핵심 2: 시스템 파이썬 대신 /venv 안의 파이썬을 기본으로 사용하도록 PATH 변경
    PATH="/venv/bin:$PATH"

RUN apt-get update && apt-get install -y \
    build-essential \
    graphviz \
    libgraphviz-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 3. 최신 uv 설치 (공식 권장 방식)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv pip install pygraphviz --system


# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. 의존성 파일 복사 및 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 6. 프로젝트 전체 코드 복사
COPY . .

# 7. 포트 노출
EXPOSE 8000

# 8. 컨테이너 실행 시 Django 서버 가동
# 이제 PATH가 변경되어 자동으로 /venv/bin/python 이 실행됩니다!
CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:8000"]