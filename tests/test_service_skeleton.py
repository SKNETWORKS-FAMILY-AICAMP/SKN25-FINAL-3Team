"""서비스 skeleton이 import와 기본 실행을 통과하는지 확인하는 테스트입니다."""
from backend.fastapi.app.main import app
from agents.graph import build_default_adapters, run_service_pipeline


def test_fastapi_app_imports():
    assert app.title == "Patent AI Agent Service"


def test_service_pipeline_smoke():
    state = run_service_pipeline(
        "AI 기반 특허 문서 작성 보조 시스템으로 문제, 해결수단, 효과를 구조화한다.",
        build_default_adapters(),
    )
    assert state["workflow"]["status"] in {"completed", "wait_user", "running"}
    assert "summary" in state
