from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

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
