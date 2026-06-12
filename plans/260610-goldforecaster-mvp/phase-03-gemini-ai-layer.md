# Phase 03 — Gemini AI Layer (Epic 3)

**Priority:** P1 | **Status:** Completed | **Effort:** ~60h

## Context Links

- PRD Epic 3: `docs/2_prd.md`
- Architecture AI Layer: `docs/3_architecture.md`
- Depends on: Phase 02 (articles + macro in DB)

## Overview

`summarizer.py` + `predictor.py` using Gemini Flash only. Structured JSON output. Forecast triggered only on new data. Cost-aware caching.

## Key Insights

- Free tier → **one model** `gemini-2.0-flash` (or latest Flash in AI Studio) for both tasks
- PRD mentions Advanced/Ultra — **skip for MVP**, document in code comments
- Structured output via Gemini `response_schema` / JSON mode
- Batch summarize: max N articles per run, skip already-summarized (`summary IS NULL`)
- Super prompt: summarized news + macro + recent gold price trend (last 7 days from DB)

## Requirements

**Functional**
- `summarizer.py` — input raw article text → bullet summary + sentiment (`bullish|bearish|neutral`)
- `predictor.py` — aggregate context → 4 horizons JSON:
  ```json
  {
    "day":   {"trend": "up|down|sideways", "confidence": 0-100, "reasoning": "..."},
    "week":  {...},
    "month": {...},
    "quarter": {...}
  }
  ```
- No absolute price predictions in prompt or output schema
- Cache: don't re-forecast if no new articles/macro since last `forecasts.created_at`
- CLI: `python main.py --run-pipeline` (scrape → summarize → predict)
- Store results in `articles.summary`, `articles.sentiment`, `forecasts` table

**Non-Functional**
- Respect Gemini RPM — sequential or small batch with delay
- Token budget: truncate article body to ~4K chars before summarize

## Architecture

```
ingestion complete
       │
       ▼
summarizer.py ──► Gemini Flash ──► UPDATE articles
       │
       ▼ (if new data flag)
predictor.py ──► Gemini Flash + response_schema ──► INSERT forecasts
```

**Meta-prompt structure (predictor):**
1. System: gold macro analyst, trend-only, no price targets
2. Context block: latest macro snapshot (DXY, US10Y, SPDR, gold)
3. News block: top 10 summarized articles by recency + sentiment distribution
4. Price context: 7-day gold direction from `macro_snapshots`
5. Output: strict JSON schema 4 horizons

## Related Code Files

| Action | Path |
|--------|------|
| Create | `src/backend/services/summarizer.py` |
| Create | `src/backend/services/predictor.py` |
| Create | `src/backend/core/prompts.py` |
| Modify | `src/backend/adapters/gemini_client.py` — add `generate_json()` |
| Modify | `main.py` — `--run-pipeline`, `--summarize`, `--forecast` |
| Create | `tests/test_predictor_schema.py` |
| Create | `tests/test_summarizer.py` (mock Gemini) |

## Implementation Steps

1. **prompts.py** — versioned prompt templates (SUMMARIZE_V1, FORECAST_V1)
2. **gemini_client.generate_json()** — wrap SDK with schema validation via Pydantic
3. **summarizer** — fetch unsummarized articles, loop with rate limit sleep
4. **predictor** — `has_new_data()` check vs last forecast timestamp
5. **Context builder** — SQL queries assembling prompt context
6. **Validation** — Pydantic models `ForecastHorizon`, `ForecastResult`
7. **CLI integration** — `--run-pipeline` chains Phase 2 + 3
8. **Error handling** — 429 → exponential backoff, log, exit graceful
9. **Tests** — mock responses, assert JSON schema; golden-file prompt snapshot optional

## Todo List

- [x] Prompt templates
- [x] Pydantic output models
- [x] Summarizer service
- [x] New-data gate for predictor
- [x] Predictor + 4-horizon schema
- [x] CLI pipeline command
- [x] Rate limit handling
- [x] Unit tests with mocks

## Success Criteria

- Unsummarized article → summary + sentiment in DB
- `--forecast` produces valid 4-horizon JSON
- Re-run forecast without new data → skip (log "cached")
- No numeric gold price target in any output field
- `--run-pipeline` end-to-end from scrape to forecast

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Hallucination | Schema enforcement, prompt forbids price targets |
| 429 rate limit | Queue, 6s between calls, daily cap monitor |
| Token overflow | Truncate articles, top-N news only |
| Inconsistent sentiment | Enum constraint in schema |

## Security Considerations

- Sanitize article HTML before prompt (no script injection)
- API key server-side only

## Next Steps

→ Phase 04: expose `/api/forecasts`, `/api/news`, `/api/macro` for dashboard
