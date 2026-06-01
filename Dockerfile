FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    APP_WORKERS=2

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY agents ./agents
COPY backend ./backend
COPY pyproject.toml ./pyproject.toml

RUN useradd --create-home --shell /usr/sbin/nologin patent \
    && mkdir -p /app/artifacts /app/data \
    && chown -R patent:patent /app
USER patent

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${APP_PORT}/health" || exit 1

CMD ["sh", "-c", "uvicorn backend.fastapi.app.main:app --host ${APP_HOST} --port ${APP_PORT} --workers ${APP_WORKERS}"]
