"""Integration tests for dashboard API endpoints."""

from fastapi.testclient import TestClient

from src.backend.api.app import create_app
from src.backend.core.database import get_connection, insert_article, insert_macro_snapshot


def test_dashboard_api_shapes(temp_db, sample_macro):
    with get_connection() as conn:
        insert_article(
            conn,
            source="fed",
            url="https://example.com/fed-release",
            url_hash="hash-fed",
            title="FOMC holds rates steady",
            body="The Federal Reserve kept rates unchanged.",
            published_at=None,
        )
        conn.execute(
            """
            UPDATE articles
            SET summary = '- Rates unchanged', sentiment = 'neutral'
            WHERE url = 'https://example.com/fed-release'
            """
        )
        conn.execute(
            """
            INSERT INTO forecasts (horizon, trend, confidence, reasoning)
            VALUES
              ('day', 'sideways', 60, 'Rates on hold'),
              ('week', 'up', 65, 'Dollar softening'),
              ('month', 'up', 70, 'Macro support'),
              ('quarter', 'sideways', 55, 'Mixed outlook')
            """
        )

    client = TestClient(create_app())

    macro = client.get("/api/macro/latest")
    assert macro.status_code == 200
    assert macro.json()["gold_spot"] == 2340.0

    history = client.get("/api/macro/history?days=7")
    assert history.status_code == 200
    assert len(history.json()["points"]) >= 1

    news = client.get("/api/news?sentiment=neutral")
    assert news.status_code == 200
    assert news.json()["count"] == 1

    forecasts = client.get("/api/forecasts/latest")
    assert forecasts.status_code == 200
    payload = forecasts.json()
    assert len(payload["horizons"]) == 4
    assert payload["horizons"][0]["confidence"] >= 0
