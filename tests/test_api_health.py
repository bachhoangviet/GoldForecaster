"""API health endpoint tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.backend.api.app import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "api-test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from src.backend.core.config import get_settings

    get_settings.cache_clear()
    app = create_app()
    yield TestClient(app)
    get_settings.cache_clear()


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
