"""backend/fastapi/app/routers/pipeline.py 단위 테스트.

DB, Redis, run_service_pipeline을 전부 mock합니다.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from agents.state import create_initial_state
from backend.fastapi.app.db import get_db
from backend.fastapi.app.main import app


@pytest.fixture
def mock_db(mock_db_session):
    """get_db 의존성을 mock session으로 교체합니다."""
    app.dependency_overrides[get_db] = lambda: mock_db_session
    yield mock_db_session
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_db) -> TestClient:
    return TestClient(app)


@pytest.fixture
def completed_state():
    state = create_initial_state("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.")
    state["workflow"]["status"] = "completed"
    state["summary"] = {"status": "ok", "summary": "요약"}
    state["master_decision"] = {"status": "completed", "next_agent": "end"}
    return state


# ── GET /health 테스트 ─────────────────────────────────────────────────────

def test_health_endpoint_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── POST /api/pipeline/run 테스트 ──────────────────────────────────────────

def test_pipeline_run_returns_run_id(client, completed_state):
    with patch(
        "backend.fastapi.app.routers.pipeline.run_service_pipeline",
        return_value=completed_state,
    ):
        response = client.post(
            "/api/pipeline/run",
            json={"user_input": "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다."},
        )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert len(data["run_id"]) > 0


def test_pipeline_run_returns_state(client, completed_state):
    with patch(
        "backend.fastapi.app.routers.pipeline.run_service_pipeline",
        return_value=completed_state,
    ):
        response = client.post(
            "/api/pipeline/run",
            json={"user_input": "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다."},
        )
    data = response.json()
    assert "state" in data
    assert data["state"]["workflow"]["status"] == "completed"


def test_pipeline_run_stores_run_id_in_state(client, completed_state):
    with patch(
        "backend.fastapi.app.routers.pipeline.run_service_pipeline",
        return_value=completed_state,
    ):
        response = client.post(
            "/api/pipeline/run",
            json={"user_input": "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다."},
        )
    data = response.json()
    assert data["state"]["run_session"]["run_id"] == data["run_id"]


def test_pipeline_run_empty_input_returns_422(client):
    response = client.post("/api/pipeline/run", json={"user_input": ""})
    assert response.status_code == 422


def test_pipeline_run_missing_body_returns_422(client):
    response = client.post("/api/pipeline/run", json={})
    assert response.status_code == 422


def test_pipeline_run_saves_to_db(client, mock_db, completed_state):
    with patch(
        "backend.fastapi.app.routers.pipeline.run_service_pipeline",
        return_value=completed_state,
    ):
        client.post(
            "/api/pipeline/run",
            json={"user_input": "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다."},
        )
    mock_db.add.assert_called_once()
    assert mock_db.commit.call_count >= 2  # run 생성 + 최종 업데이트


def test_pipeline_run_with_custom_route(client, completed_state):
    with patch(
        "backend.fastapi.app.routers.pipeline.run_service_pipeline",
        return_value=completed_state,
    ) as mock_pipeline:
        client.post(
            "/api/pipeline/run",
            json={
                "user_input": "충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.",
                "route": ["summary"],
            },
        )
    _, kwargs = mock_pipeline.call_args
    assert kwargs.get("route") == ("summary",)


# ── POST /api/pipeline/continue 테스트 ────────────────────────────────────

def test_pipeline_continue_appends_user_input(client, completed_state):
    state = create_initial_state("기존 입력")
    state["summary"] = {"status": "ok", "summary": "기존 요약"}
    state["workflow"]["status"] = "wait_user"

    with patch(
        "backend.fastapi.app.routers.pipeline.run_service_pipeline",
        return_value=completed_state,
    ):
        response = client.post(
            "/api/pipeline/continue",
            json={"state": state, "user_input": "추가 입력"},
        )
    assert response.status_code == 200


def test_pipeline_continue_without_user_input(client, completed_state):
    state = create_initial_state("충분히 긴 발명 설명입니다. 30자 이상이어야 합니다.")
    state["summary"] = {"status": "ok", "summary": "기존 요약"}

    with patch(
        "backend.fastapi.app.routers.pipeline.run_service_pipeline",
        return_value=completed_state,
    ):
        response = client.post(
            "/api/pipeline/continue",
            json={"state": state},
        )
    assert response.status_code == 200
