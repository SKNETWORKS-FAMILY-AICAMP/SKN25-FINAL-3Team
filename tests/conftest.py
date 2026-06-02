"""pytest 공유 fixture 모음.

DATABASE_URL을 임포트 전에 설정해야 db.py의 RuntimeError를 피할 수 있습니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가합니다.
# pyproject.toml의 pythonpath 설정보다 conftest.py가 먼저 로딩되는 경우를 대비합니다.
_ROOT = Path(__file__).resolve().parent.parent
# 중복을 허용하고 무조건 삽입합니다 (pytest의 로딩 순서 관계없이 동작 보장)
sys.path.insert(0, str(_ROOT))

import os

# db.py가 임포트될 때 DATABASE_URL이 없으면 RuntimeError가 발생합니다.
# 실제 DB에 연결하지 않으므로 dummy 값으로 충분합니다.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from agents.state import PatentAgentState, create_initial_state


# ── State fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def empty_state() -> PatentAgentState:
    return create_initial_state()


@pytest.fixture
def state_with_input() -> PatentAgentState:
    return create_initial_state(
        "AI 기반 문서 자동 분류 시스템으로 정확도와 처리 속도를 동시에 향상시킨다."
    )


@pytest.fixture
def state_with_summary(state_with_input: PatentAgentState) -> PatentAgentState:
    """summary agent 결과가 채워진 state."""
    state_with_input["summary"] = {
        "status": "ok",
        "project_name": "AI 문서 분류 시스템",
        "problem_to_solve": "기존 수동 분류의 낮은 정확도",
        "core_technology": "딥러닝 기반 분류 모델",
        "expected_effect": "정확도 95% 이상",
        "readable_summary": "AI 기반 문서 자동 분류 시스템",
        "structured_invention": {
            "title": "AI 문서 분류 시스템",
            "problem": "기존 수동 분류의 낮은 정확도",
            "solution": "딥러닝 기반 분류 모델",
            "clarification_questions": [],
        },
        "warnings": [],
    }
    return state_with_input


@pytest.fixture
def full_pipeline_state(state_with_summary: PatentAgentState) -> PatentAgentState:
    """모든 agent 결과가 채워진 state."""
    state_with_summary["prior_art"] = {"status": "ok", "summary": "선행기술 결과"}
    state_with_summary["claims"] = {"status": "ok", "summary": "청구항 결과"}
    state_with_summary["drawings"] = {"status": "ok", "summary": "도면 결과"}
    state_with_summary["specification"] = {"status": "ok", "summary": "명세서 결과"}
    state_with_summary["final_package"] = {"status": "ok", "summary": "최종 패키지"}
    return state_with_summary


# ── Mock DB/Redis fixtures ──────────────────────────────────────────────────

@pytest.fixture
def mock_db_session() -> MagicMock:
    """SQLAlchemy Session mock."""
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    return session


@pytest.fixture
def mock_run_record() -> MagicMock:
    """DB에서 조회된 Run 레코드 mock."""
    run = MagicMock()
    run.run_id = "test-run-id-1234"
    run.status = "completed"
    run.user_input = "테스트 발명 설명"
    run.errors = []
    run.state = {
        "workflow": {
            "status": "completed",
            "current_agent": "composer",
            "trace": [{"agent": "summary", "action": "run"}],
            "errors": [],
        },
        "master_decision": {"status": "completed", "next_agent": "end"},
    }
    run.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    run.updated_at = datetime(2025, 1, 2, tzinfo=timezone.utc)
    return run


@pytest.fixture
def make_mock_adapter():
    def _factory(agent_name: str, state_key: str, result: dict[str, Any] | None = None) -> MagicMock:
        adapter = MagicMock()
        adapter.agent_name = agent_name
        adapter.state_key = state_key
        adapter.run.return_value = result or {"status": "ok", "summary": f"{agent_name} 결과"}
        return adapter
    return _factory
