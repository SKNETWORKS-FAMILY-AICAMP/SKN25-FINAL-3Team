# backend/fastapi/main.py
import logging
import os
import sys
import uuid
import django
from fastapi import FastAPI, Request
from fastapi.responses import Response

sys.path.insert(0, os.path.join(os.getcwd(), 'backend', 'django'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# logging 먼저 설정 — django.setup()보다 앞에 두어야 초기화 로그가 포맷에 맞게 기록된다
from agents.core.logging_config import setup_logging, request_id_var
setup_logging()

django.setup()

from backend.fastapi.routers import claims, drawings, specification

logger = logging.getLogger(__name__)

# ── Phoenix / OpenTelemetry 계측 설정 ──────────────────────────────────────
_phoenix_initialized = False


def _setup_phoenix() -> str | None:
    """Phoenix OTLP 익스포터 + LangChain 자동 계측 초기화. 실패해도 앱은 정상 기동."""
    global _phoenix_initialized
    if _phoenix_initialized:
        return None  # --reload 재시작 등 중복 호출 방지

    try:
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from openinference.instrumentation.langchain import LangChainInstrumentor

        endpoint = os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "http://phoenix:6006/v1/traces",  # docker-compose 기본값
        )

        resource = Resource(attributes={"service.name": "patent-ai-worker"})
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        LangChainInstrumentor().instrument()
        _phoenix_initialized = True
        return endpoint
    except Exception as exc:  # noqa: BLE001
        logger.warning("Phoenix 계측 초기화 실패 (모니터링 없이 계속): %s", exc)
        return None


# ── FastAPI 앱 ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Patent AI Worker",
    description="특허 생성 AI 워커 FastAPI 서버",
    version="1.0.0",
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next) -> Response:
    """요청마다 X-Request-ID를 생성·주입해 로그와 트레이스를 연결한다."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(claims.router, prefix="/api/v1", tags=["Claims & Prior Art"])
app.include_router(drawings.router, prefix="/api/v1", tags=["Drawings"])
app.include_router(specification.router, prefix="/api/v1", tags=["Specification"])


@app.on_event("startup")
async def startup_event():
    phoenix_endpoint = _setup_phoenix()
    if phoenix_endpoint:
        logger.info("Phoenix 모니터링 활성화 → %s", phoenix_endpoint.replace("/v1/traces", ""))
    logger.info("FastAPI AI Worker 가동 완료!")