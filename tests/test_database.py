"""Unit tests for SQLite database layer."""

import sqlite3
from pathlib import Path

import pytest

from src.backend.core.database import get_table_counts, init_db


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    from src.backend.core.config import get_settings

    get_settings.cache_clear()
    yield db_file
    get_settings.cache_clear()


def test_init_db_creates_tables(temp_db: Path):
    init_db(temp_db)

    conn = sqlite3.connect(temp_db)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert "articles" in tables
    assert "macro_snapshots" in tables
    assert "forecasts" in tables
    assert "scrape_runs" in tables


def test_get_table_counts_empty(temp_db: Path):
    init_db(temp_db)
    counts = get_table_counts()
    assert counts["articles"] == 0
    assert counts["macro_snapshots"] == 0
