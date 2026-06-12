"""SQLite database engine with WAL mode and schema initialization."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from src.backend.core.config import get_settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    url_hash TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    summary TEXT,
    sentiment TEXT CHECK (sentiment IN ('bullish', 'bearish', 'neutral')),
    published_at TEXT,
    scraped_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON articles(scraped_at);

CREATE TABLE IF NOT EXISTS macro_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dxy REAL,
    us10y REAL,
    spdr_holdings REAL,
    gold_spot REAL,
    recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_macro_recorded_at ON macro_snapshots(recorded_at);

CREATE TABLE IF NOT EXISTS forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    horizon TEXT NOT NULL CHECK (horizon IN ('day', 'week', 'month', 'quarter')),
    trend TEXT NOT NULL CHECK (trend IN ('up', 'down', 'sideways')),
    confidence INTEGER NOT NULL CHECK (confidence BETWEEN 0 AND 100),
    reasoning TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_forecasts_created_at ON forecasts(created_at);

CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    error TEXT,
    duration_ms INTEGER,
    started_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_scrape_runs_started_at ON scrape_runs(started_at);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Create tables and enable WAL mode."""
    path = db_path or get_settings().database_file
    with _connect(path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection with schema ensured."""
    path = db_path or get_settings().database_file
    init_db(path)
    conn = _connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_table_counts() -> dict[str, int]:
    """Return row counts for core tables (CLI/debug helper)."""
    tables = ("articles", "macro_snapshots", "forecasts", "scrape_runs")
    counts: dict[str, int] = {}
    with get_connection() as conn:
        for table in tables:
            row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
            counts[table] = int(row["c"]) if row else 0
    return counts


def insert_article(
    conn: sqlite3.Connection,
    *,
    source: str,
    url: str,
    url_hash: str,
    title: str,
    body: str,
    published_at: str | None,
) -> bool:
    """Insert article if URL is new. Returns True when inserted."""
    existing = conn.execute(
        "SELECT id FROM articles WHERE url = ? OR url_hash = ?",
        (url, url_hash),
    ).fetchone()
    if existing:
        return False

    conn.execute(
        """
        INSERT INTO articles (source, url, url_hash, title, body, published_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (source, url, url_hash, title, body, published_at),
    )
    return True


def insert_macro_snapshot(
    conn: sqlite3.Connection,
    *,
    dxy: float | None,
    us10y: float | None,
    spdr_holdings: float | None,
    gold_spot: float | None,
) -> None:
    conn.execute(
        """
        INSERT INTO macro_snapshots (dxy, us10y, spdr_holdings, gold_spot)
        VALUES (?, ?, ?, ?)
        """,
        (dxy, us10y, spdr_holdings, gold_spot),
    )


def log_scrape_run(
    conn: sqlite3.Connection,
    *,
    source: str,
    status: str,
    error: str | None,
    duration_ms: int | None,
) -> None:
    conn.execute(
        """
        INSERT INTO scrape_runs (source, status, error, duration_ms)
        VALUES (?, ?, ?, ?)
        """,
        (source, status, error, duration_ms),
    )


def get_latest_macro() -> dict[str, object] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT dxy, us10y, spdr_holdings, gold_spot, recorded_at
            FROM macro_snapshots
            ORDER BY recorded_at DESC
            LIMIT 1
            """
        ).fetchone()
    if not row:
        return None
    return dict(row)


def get_unsummarized_count() -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM articles WHERE summary IS NULL"
        ).fetchone()
    return int(row["c"]) if row else 0


def get_unsummarized_articles(limit: int = 20) -> list[dict[str, object]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, source, title, body
            FROM articles
            WHERE summary IS NULL
            ORDER BY scraped_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def update_article_summary(
    conn: sqlite3.Connection,
    *,
    article_id: int,
    summary: str,
    sentiment: str,
) -> None:
    conn.execute(
        """
        UPDATE articles
        SET summary = ?, sentiment = ?
        WHERE id = ?
        """,
        (summary, sentiment, article_id),
    )


def get_recent_summarized_articles(limit: int = 10) -> list[dict[str, object]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT source, title, summary, sentiment, scraped_at
            FROM articles
            WHERE summary IS NOT NULL
            ORDER BY scraped_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_gold_price_history(limit: int = 7) -> list[dict[str, object]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT gold_spot, recorded_at
            FROM macro_snapshots
            WHERE gold_spot IS NOT NULL
            ORDER BY recorded_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_last_forecast_timestamp() -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(created_at) AS ts FROM forecasts"
        ).fetchone()
    if not row or not row["ts"]:
        return None
    return str(row["ts"])


def has_new_data_since_last_forecast() -> bool:
    last = get_last_forecast_timestamp()
    if last is None:
        with get_connection() as conn:
            has_articles = conn.execute(
                "SELECT 1 FROM articles WHERE summary IS NOT NULL LIMIT 1"
            ).fetchone()
            has_macro = conn.execute(
                "SELECT 1 FROM macro_snapshots LIMIT 1"
            ).fetchone()
        return bool(has_articles or has_macro)

    with get_connection() as conn:
        new_articles = conn.execute(
            "SELECT 1 FROM articles WHERE scraped_at > ? LIMIT 1",
            (last,),
        ).fetchone()
        new_macro = conn.execute(
            "SELECT 1 FROM macro_snapshots WHERE recorded_at > ? LIMIT 1",
            (last,),
        ).fetchone()
        new_summaries = conn.execute(
            """
            SELECT 1 FROM articles
            WHERE summary IS NOT NULL AND scraped_at > ?
            LIMIT 1
            """,
            (last,),
        ).fetchone()
    return bool(new_articles or new_macro or new_summaries)


def insert_forecasts(
    conn: sqlite3.Connection,
    *,
    day_trend: str,
    day_confidence: int,
    day_reasoning: str,
    week_trend: str,
    week_confidence: int,
    week_reasoning: str,
    month_trend: str,
    month_confidence: int,
    month_reasoning: str,
    quarter_trend: str,
    quarter_confidence: int,
    quarter_reasoning: str,
) -> None:
    rows = [
        ("day", day_trend, day_confidence, day_reasoning),
        ("week", week_trend, week_confidence, week_reasoning),
        ("month", month_trend, month_confidence, month_reasoning),
        ("quarter", quarter_trend, quarter_confidence, quarter_reasoning),
    ]
    for horizon, trend, confidence, reasoning in rows:
        conn.execute(
            """
            INSERT INTO forecasts (horizon, trend, confidence, reasoning)
            VALUES (?, ?, ?, ?)
            """,
            (horizon, trend, confidence, reasoning),
        )


def get_macro_history(days: int = 30) -> list[dict[str, object]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT gold_spot, dxy, us10y, recorded_at
            FROM macro_snapshots
            WHERE gold_spot IS NOT NULL
              AND recorded_at >= datetime('now', ?)
            ORDER BY recorded_at ASC
            """,
            (f"-{days} days",),
        ).fetchall()
    return [dict(row) for row in rows]


def get_summarized_articles(
    *,
    limit: int = 50,
    sentiment: str | None = None,
) -> list[dict[str, object]]:
    query = """
        SELECT id, source, title, summary, sentiment, scraped_at, published_at
        FROM articles
        WHERE summary IS NOT NULL
    """
    params: list[object] = []
    if sentiment:
        query += " AND sentiment = ?"
        params.append(sentiment)
    query += " ORDER BY scraped_at DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_latest_forecasts() -> list[dict[str, object]]:
    last = get_last_forecast_timestamp()
    if not last:
        return []

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT horizon, trend, confidence, reasoning, created_at
            FROM forecasts
            WHERE created_at = ?
            ORDER BY CASE horizon
                WHEN 'day' THEN 1
                WHEN 'week' THEN 2
                WHEN 'month' THEN 3
                WHEN 'quarter' THEN 4
                ELSE 5
            END
            """,
            (last,),
        ).fetchall()
    return [dict(row) for row in rows]
