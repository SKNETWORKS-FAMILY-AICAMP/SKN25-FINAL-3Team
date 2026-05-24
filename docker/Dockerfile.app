# Django + Agents 공용 이미지
# 사용처: django 서비스, fastapi 서비스

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.7.*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 소스 복사
# TODO: fastapi와 django 소스 분리
COPY . .

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app
