# Phase 05 — Testing & Operations (Epic 5)

**Priority:** P2 | **Status:** Completed | **Effort:** ~60h

## Context Links

- PRD Epic 5: `docs/2_prd.md`
- Depends on: Phases 01-04 complete

## Overview

Integration tests full pipeline, error resilience, scheduler reliability, developer docs, optional Docker shell for future cloud.

## Key Insights

- MVP local — no CI required but pytest suite valuable
- Integration test uses fixtures/mocks for external APIs (no live scrape in CI)
- `--run-scraper` dry-run mode already useful for ops

## Requirements

**Functional**
- Integration test: fixture articles → summarize → forecast → assert JSON schema
- Integration test: ingestion orchestrator with mocked HTTP/Playwright
- Network failure test: retry logic fires 3x
- Scheduler runs without duplicate overlapping jobs
- README complete: setup, env vars, daily dev workflow, troubleshooting scrapers
- Optional: `Dockerfile` + `docker-compose.yml` (backend + frontend) for future deploy

**Non-Functional**
- `pytest` full suite < 2 min (no live network)
- Logs structured enough to debug scraper failures

## Architecture

```
tests/
├── conftest.py              # fixtures, temp SQLite
├── unit/
│   ├── test_gemini_client.py
│   ├── test_scrapers_kitco.py
│   └── test_predictor_schema.py
└── integration/
    ├── test_pipeline_e2e.py
    └── test_api_endpoints.py
```

## Related Code Files

| Action | Path |
|--------|------|
| Create | `tests/integration/test_pipeline_e2e.py` |
| Create | `tests/integration/test_api_endpoints.py` |
| Create | `tests/conftest.py` |
| Create | `docker-compose.yml` (optional) |
| Modify | `README.md` — full dev guide |
| Modify | `src/backend/services/ingestion.py` — overlap guard for scheduler |

## Implementation Steps

1. **conftest.py** — temp DB, sample articles, mock Gemini client fixture
2. **test_pipeline_e2e** — insert raw articles → summarize → forecast → verify DB state
3. **test_api_endpoints** — FastAPI TestClient, assert response shapes
4. **test_retry** — mock requests raising ConnectionError, assert 3 retries
5. **Scheduler guard** — `max_instances=1` on APScheduler jobs
6. **Logging** — consistent format: `[source] status duration`
7. **README sections** — Prerequisites, Quick Start, CLI reference, Scraper maintenance, Gemini quota tips
8. **docker-compose** (optional) — Python service + Node service + volume for SQLite
9. **Manual test checklist** — document in README

## Todo List

- [x] Test fixtures + conftest
- [x] E2E pipeline test (mocked externals)
- [x] API endpoint tests
- [x] Retry unit test
- [x] Scheduler overlap prevention
- [x] README complete
- [x] Optional Docker compose
- [x] Manual QA checklist

## Success Criteria

- `pytest` passes all tests without network
- Pipeline test validates 4-horizon forecast schema
- Scheduler doesn't stack concurrent scrapes
- New developer can setup from README in < 30 min
- All PRD CLI flags documented and working

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Flaky integration tests | No live HTTP in CI, fixtures only |
| Docker complexity | Optional, not blocking MVP |

## Security Considerations

- Test fixtures contain no real API keys
- `.env.test` example with dummy values

## Next Steps

MVP complete. Post-MVP per project brief:
- Telegram alerts
- LSTM/ARIMA parallel scoring
- PDF report ingestion
