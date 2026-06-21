import logging

# agents.core 패키지가 임포트되는 순간 핸들러가 없으면 setup_logging()을 호출한다.
# 이를 통해 CLI·테스트 등 FastAPI 없이 에이전트를 실행해도 로그가 유실되지 않는다.
# FastAPI가 먼저 setup_logging()을 호출한 경우에는 이미 핸들러가 있으므로 건너뛴다.
if not logging.root.handlers:
    from agents.core.logging_config import setup_logging
    setup_logging()