"""서비스형 Composer agent 패키지입니다.

패키지 import 시 LangChain/OpenAI 의존 구현을 자동 로드하지 않도록 가볍게 유지합니다.
실제 agent 함수가 필요하면 `agents.composer.composer_agent`에서 직접 가져옵니다.
"""

__all__: list[str] = []
