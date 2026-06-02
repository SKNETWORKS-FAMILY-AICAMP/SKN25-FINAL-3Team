"""backend/fastapi/app/routers/runs.py 단위 테스트.

DB와 Redis를 전부 mock합니다.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.fastapi.app.main import app


# ── GET /api/runs/{run_id} 테스트 ─────────────────────────────────────────

def test_get_run_not_found_returns_404(client, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    response = client.get("/api/runs/nonexistent-id")
    assert response.status_code == 404


def test_get_run_returns_run_data(client, mock_db, mock_run_record):
    mock_db.query.return_value.filter.return_value.first.return_value = mock_run_record

    with patch("backend.fastapi.app.routers.runs._redis") as mock_redis:
        mock_redis.get.return_value = None
        response = client.get("/api/runs/test-run-id-1234")

    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "test-run-id-1234"
    assert data["status"] == "completed"


def test_get_run_includes_current_agent_from_redis(client, mock_db, mock_run_record):
    mock_run_record.status = "running"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_run_record

    with patch("backend.fastapi.app.routers.runs._redis") as mock_redis:
        mock_redis.get.return_value = "claim"
        response = client.get("/api/runs/test-run-id-1234")

    assert response.json()["current_agent"] == "claim"


def test_get_run_fallback_to_db_when_redis_fails(client, mock_db, mock_run_record):
    mock_run_record.status = "completed"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_run_record

    with patch("backend.fastapi.app.routers.runs._redis") as mock_redis:
        mock_redis.get.side_effect = Exception("Redis 연결 실패")
        response = client.get("/api/runs/test-run-id-1234")

    assert response.status_code == 200
    # Redis 실패 시 DB state에서 current_agent를 읽어야 합니다
    assert response.json()["current_agent"] == "composer"


def test_get_run_completed_agents_from_trace(client, mock_db, mock_run_record):
    mock_db.query.return_value.filter.return_value.first.return_value = mock_run_record

    with patch("backend.fastapi.app.routers.runs._redis") as mock_redis:
        mock_redis.get.return_value = None
        response = client.get("/api/runs/test-run-id-1234")

    data = response.json()
    assert "summary" in data["completed_agents"]


def test_get_run_errors_empty_by_default(client, mock_db, mock_run_record):
    mock_run_record.errors = []
    mock_db.query.return_value.filter.return_value.first.return_value = mock_run_record

    with patch("backend.fastapi.app.routers.runs._redis") as mock_redis:
        mock_redis.get.return_value = None
        response = client.get("/api/runs/test-run-id-1234")

    assert response.json()["errors"] == []


def test_get_run_includes_timestamps(client, mock_db, mock_run_record):
    mock_db.query.return_value.filter.return_value.first.return_value = mock_run_record

    with patch("backend.fastapi.app.routers.runs._redis") as mock_redis:
        mock_redis.get.return_value = None
        response = client.get("/api/runs/test-run-id-1234")

    data = response.json()
    assert data["created_at"] is not None
    assert data["updated_at"] is not None
