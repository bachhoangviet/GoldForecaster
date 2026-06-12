"""API route tests for dashboard endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.backend.api.app import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "api-routes.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from src.backend.core.config import get_settings
    from src.backend.core.database import get_connection, insert_article, insert_macro_snapshot

    get_settings.cache_clear()

    with get_connection() as conn:
        insert_macro_snapshot(
            conn,
            dxy=121.5,
            us10y=4.25,
            spdr_holdings=900.0,
            gold_spot=2345.6,
        )
        insert_article(
            conn,
            source="kitco",
            url="https://example.com/news-1",
            url_hash="hash-1",
            title="Gold rises",
            body="Gold moved higher.",
            published_at=None,
        )
        conn.execute(
            """
            UPDATE articles
            SET summary = '- Dollar weakness', sentiment = 'bullish'
            WHERE url = 'https://example.com/news-1'
            """
        )
        conn.execute(
            """
            INSERT INTO forecasts (horizon, trend, confidence, reasoning)
            VALUES
              ('day', 'up', 70, 'Risk-off flows'),
              ('week', 'up', 65, 'Macro support'),
              ('month', 'sideways', 55, 'Mixed signals'),
              ('quarter', 'sideways', 50, 'Range bound')
            """
        )

    app = create_app()
    yield TestClient(app)
    get_settings.cache_clear()


def test_macro_latest(client: TestClient):
    response = client.get("/api/macro/latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["gold_spot"] == 2345.6
    assert payload["dxy"] == 121.5


def test_macro_history(client: TestClient):
    response = client.get("/api/macro/history?days=30")
    assert response.status_code == 200
    payload = response.json()
    assert payload["days"] == 30
    assert len(payload["points"]) == 1


def test_news_list_and_filter(client: TestClient):
    all_news = client.get("/api/news")
    assert all_news.status_code == 200
    assert all_news.json()["count"] == 1

    bullish = client.get("/api/news?sentiment=bullish")
    assert bullish.status_code == 200
    assert bullish.json()["count"] == 1

    bearish = client.get("/api/news?sentiment=bearish")
    assert bearish.status_code == 200
    assert bearish.json()["count"] == 0


def test_forecasts_latest(client: TestClient):
    response = client.get("/api/forecasts/latest")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["horizons"]) == 4
    assert payload["horizons"][0]["horizon"] == "day"
