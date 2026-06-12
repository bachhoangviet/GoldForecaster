"""Domain models for ingestion and storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256


class ScrapeStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class RawArticle:
    source: str
    url: str
    title: str
    body: str
    published_at: str | None = None

    @property
    def url_hash(self) -> str:
        return sha256(self.url.encode("utf-8")).hexdigest()


@dataclass
class MacroSnapshot:
    dxy: float | None = None
    us10y: float | None = None
    spdr_holdings: float | None = None
    gold_spot: float | None = None
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ScrapeRunRecord:
    source: str
    status: ScrapeStatus
    error: str | None = None
    duration_ms: int | None = None
    article_count: int = 0


@dataclass
class IngestionReport:
    articles_inserted: int = 0
    articles_skipped: int = 0
    macro_saved: bool = False
    scrape_runs: list[ScrapeRunRecord] = field(default_factory=list)

    @property
    def sources_succeeded(self) -> int:
        return sum(1 for r in self.scrape_runs if r.status == ScrapeStatus.SUCCESS)

    @property
    def sources_failed(self) -> int:
        return sum(1 for r in self.scrape_runs if r.status == ScrapeStatus.FAILED)
