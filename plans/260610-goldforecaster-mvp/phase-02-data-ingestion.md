# Phase 02 — Data Ingestion Pipeline (Epic 2)

**Priority:** P1 | **Status:** Completed | **Effort:** ~80h

## Context Links

- PRD Epic 2: `docs/2_prd.md`
- Adapters: `docs/3_architecture.md` § Data Ingestion Layer
- Depends on: Phase 01 (database, config, CLI)

## Overview

Scrape 5 news sources + ingest macro data (DXY, US10Y, SPDR, gold spot). Normalize, dedupe, store SQLite. Async/multi-thread ≤5 min total.

## Key Insights

- Kitco/FED/CNBC → BeautifulSoup viable
- Reuters/Bloomberg → Playwright headless required
- Macro → FRED API free (`DGS10` US10Y, `DTWEXBGS` trade-weighted USD index as DXY proxy)
- Gold spot → Kitco price page scrape
- SPDR → scrape `ssga.com` GLD holdings or `yfinance` ticker `GLD` as fallback

## Requirements

**Functional**
- `web_scrapers.py` — adapter per source implementing `ScraperAdapter` interface
- `market_api.py` — FRED async fetch + gold/SPDR adapters
- Normalize: strip HTML, extract title/body/url/published_at
- Dedupe by URL hash before insert
- `main.py --run-scraper` runs all adapters, logs to `scrape_runs`
- `main.py --show-data` prints latest macro + article count
- Scheduler stub: APScheduler 4x/day news, hourly macro (configurable)

**Non-Functional**
- Retry 3x, 5s backoff (PRD NFR)
- Total scrape < 5 min
- Playwright session cleanup after each run

## Architecture

```python
# Adapter interface (pseudocode)
class ScraperAdapter(Protocol):
    source: str
    async def fetch(self) -> list[RawArticle]: ...
    def parse(self, html: str) -> list[RawArticle]: ...

# Sources
KITCO, FED, CNBC     → requests + BS4
REUTERS, BLOOMBERG   → playwright async
MARKET               → FRED + kitco price + spdr
```

**Data flow:** Scheduler/CLI → orchestrator `services/ingestion.py` → adapters parallel (asyncio.gather) → normalize → SQLite

## Related Code Files

| Action | Path |
|--------|------|
| Create | `src/backend/adapters/web_scrapers.py` |
| Create | `src/backend/adapters/market_api.py` |
| Create | `src/backend/services/ingestion.py` |
| Create | `src/backend/core/models.py` (dataclasses/Pydantic) |
| Modify | `main.py` — implement `--run-scraper`, `--show-data` |
| Create | `tests/test_scrapers_kitco.py` (fixture HTML) |
| Create | `tests/test_market_api.py` (mock FRED) |

## Implementation Steps

1. **Define models** — `RawArticle`, `MacroSnapshot`, `ScrapeRun`
2. **Base scraper** — retry decorator, user-agent rotation, timeout 30s
3. **Kitco news** — list page + article links (BS4) — easiest, do first
4. **FED** — press releases / speeches RSS or HTML list
5. **CNBC** — gold/commodities section
6. **Reuters** — Playwright, navigate gold/commodities, extract headlines
7. **Bloomberg** — Playwright, markets section (expect failures — log, don't crash pipeline)
8. **market_api.py** — FRED `DGS10`, `DTWEXBGS`; Kitco gold bid; SPDR holdings
9. **ingestion.py** — orchestrate parallel fetch, merge, upsert DB
10. **APScheduler** — register jobs in `main.py --serve` or separate `worker.py`
11. **CLI** — `--run-scraper [--source kitco]` filter for debug
12. **Tests** — saved HTML fixtures for Kitco parse; mock HTTP for FRED

## Todo List

- [x] ScraperAdapter interface
- [x] Kitco + FED + CNBC (BS4)
- [x] Reuters + Bloomberg (Playwright)
- [x] FRED macro integration
- [x] Gold price + SPDR
- [x] Ingestion orchestrator
- [x] scrape_runs logging
- [x] Scheduler config
- [x] Parser fixture tests

## Success Criteria

- `--run-scraper` completes without crash (partial source failure OK, logged)
- ≥3/5 news sources return articles in dev environment
- Macro row in `macro_snapshots` with dxy, us10y, gold_spot
- Duplicate URL not inserted twice
- Full run < 5 min on typical connection

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Bloomberg/Reuters block | High | Playwright stealth, low frequency, per-source error isolation |
| DOM changes | High | `--run-scraper --source X` isolated debug |
| FRED rate limit | Low | Cache hourly, single series batch |
| SPDR source unavailable | Medium | yfinance GLD volume fallback |

## Security Considerations

- Scraper runs server-side only
- No scraped content executed as code
- Respect robots.txt where feasible (document exceptions for MVP)

## Next Steps

→ Phase 03: pass new articles to Gemini summarizer
