import contextvars
import logging
import logging.config
import os

# 요청별 ID — FastAPI 미들웨어가 세팅하면 모든 로그 레코드에 자동 포함된다
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(level: str | None = None) -> None:
    """앱 전체 로깅을 한 곳에서 설정한다. FastAPI 모듈 임포트 시점에 단 한 번 호출."""
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    is_prod = os.getenv("ENV", "dev") == "prod"

    # json formatter는 라이브러리가 실제로 설치된 경우에만 구성에 포함한다.
    # dictConfig는 formatters 딕셔너리의 모든 항목을 인스턴스화하므로,
    # 미설치 상태에서 "json" 키가 남아 있으면 ValueError로 기동이 실패한다.
    use_json = False
    if is_prod:
        try:
            import pythonjsonlogger  # noqa: F401
            use_json = True
        except ImportError:
            pass

    formatters: dict = {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s [req=%(request_id)s]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    if use_json:
        formatters["json"] = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(request_id)s %(message)s",
        }

    config: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if use_json else "standard",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"level": log_level, "handlers": ["console"]},
        # 외부 라이브러리 노이즈 억제
        "loggers": {
            "httpx": {"level": "WARNING", "propagate": True},
            "httpcore": {"level": "WARNING", "propagate": True},
            "openai": {"level": "WARNING", "propagate": True},
            "langchain": {"level": "WARNING", "propagate": True},
            "langgraph": {"level": "WARNING", "propagate": True},
            "urllib3": {"level": "WARNING", "propagate": True},
        },
    }

    logging.config.dictConfig(config)

    # dictConfig는 filter를 핸들러에 직접 등록하는 API가 불안정하므로 수동으로 주입한다
    _filter = _RequestIdFilter()
    for handler in logging.root.handlers:
        handler.addFilter(_filter)