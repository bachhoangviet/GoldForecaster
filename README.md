# GoldForecaster

AI-assisted gold market forecasting: macro data ingestion, news summarization, and multi-horizon trend analysis.

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| Git | any recent |

API keys (free tier):
- `GEMINI_API_KEY` — [Google AI Studio](https://aistudio.google.com/apikey)
- `FRED_API_KEY` — [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html)

## Quick Start (< 30 min)

```bash
# 1. Python backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
playwright install chromium

# 2. Environment
copy .env.example .env            # Windows
# cp .env.example .env            # macOS/Linux
# Edit .env → set GEMINI_API_KEY and FRED_API_KEY

# 3. Verify backend
python main.py --test-ai
python main.py --run-scraper --source kitco
python main.py --serve

# 4. Frontend dashboard (new terminal)
cd src/frontend
copy .env.example .env.local
npm install
npm run dev
```

- API health: http://127.0.0.1:8000/health
- Dashboard: http://localhost:3000

## Daily Dev Workflow

```bash
# Terminal 1 — API
python main.py --serve

# Terminal 2 — Dashboard
cd src/frontend && npm run dev

# Refresh data + AI (as needed)
python main.py --run-pipeline
python main.py --show-data
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `python main.py --test-ai` | Ping Gemini API |
| `python main.py --run-scraper` | Full news + macro ingestion |
| `python main.py --run-scraper --source kitco` | Single news source |
| `python main.py --run-scraper --macro-only` | Macro data only |
| `python main.py --summarize` | AI-summarize pending articles |
| `python main.py --forecast` | 4-horizon trend forecast |
| `python main.py --forecast --force-forecast` | Bypass forecast cache |
| `python main.py --run-pipeline` | Ingest → summarize → forecast |
| `python main.py --run-pipeline --skip-scrape` | AI only on existing DB data |
| `python main.py --show-data` | Table counts + latest macro/forecast |
| `python main.py --serve` | FastAPI on port 8000 |
| `python main.py --worker` | Scheduler (news 4x/day, macro hourly) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes (AI) | Gemini Flash API key |
| `FRED_API_KEY` | Yes (macro) | FRED macro series key |
| `DATABASE_PATH` | No | SQLite path (default `data/goldforecaster.db`) |
| `GEMINI_MODEL` | No | Default model fallback (`gemini-2.5-flash`) |
| `GEMINI_SUMMARIZE_MODELS` | No | Comma-separated summarize chain; rotates on 429 |
| `GEMINI_FORECAST_MODELS` | No | Comma-separated forecast chain; rotates on 429 |
| `GEMINI_SUMMARIZE_MODEL` | No | Primary summarize model (legacy fallback) |
| `GEMINI_FORECAST_MODEL` | No | Primary forecast model (legacy fallback) |
| `SUMMARIZE_BATCH_LIMIT` | No | Max articles per summarize run (default `100`) |
| `GEMINI_REQUEST_DELAY_SECONDS` | No | Pause between Gemini calls (default `8`) |
| `GEMINI_RATE_LIMIT_COOLDOWN_SECONDS` | No | Extra pause after 429 recovery (default `30`) |
| `GEMINI_MODEL_COOLDOWN_SECONDS` | No | Per-model cooldown after 429 before retry (default `300`) |
| `API_HOST` / `API_PORT` | No | FastAPI bind (default `127.0.0.1:8000`) |
| `NEXT_PUBLIC_API_URL` | No | Frontend API base (default `http://127.0.0.1:8000`) |

## Testing

```bash
# All tests — no live network required
pytest

# Integration only
pytest tests/integration -v
```

Test env template: copy `.env.test.example` for dummy keys.

## Troubleshooting

### Scraper returns `failed` or `partial`

| Source | Common cause | Fix |
|--------|--------------|-----|
| Reuters/Bloomberg | Anti-bot blocking | Expected locally; run `--source kitco` to debug |
| FED | XML BOM/encoding | Fixed in parser; retry `--source fed` |
| Macro | Missing `FRED_API_KEY` | Add key to `.env` |
| Kitco/CNBC | DOM change | Update selectors in `web_scrapers.py` |

Debug one source:
```bash
python main.py --run-scraper --source kitco --news-only
```

### Gemini `429` / rate limit

- Free tier ~10-15 RPM — summarizer waits 6s between calls
- Run `--summarize` in smaller batches (default 20 articles)
- Check quota in [AI Studio](https://aistudio.google.com/)

### Dashboard shows empty data

1. `python main.py --show-data` — verify articles/forecasts exist
2. Ensure API running: `python main.py --serve`
3. Check `src/frontend/.env.local` → `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`

### `database is locked`

- SQLite WAL mode enabled — avoid multiple writers
- Stop `--worker` before manual CLI runs if issues persist

## Manual QA Checklist

- [ ] `pytest` passes (all tests)
- [ ] `python main.py --test-ai` succeeds with real key
- [ ] `python main.py --run-scraper --source fed` inserts articles
- [ ] `python main.py --run-pipeline --skip-scrape` creates forecast
- [ ] `GET /api/macro/latest` returns JSON
- [ ] Dashboard loads chart, forecast tabs, news filter
- [ ] Re-run `--forecast` skips with "cached" message
- [ ] `--forecast --force-forecast` regenerates forecast

## Docker (optional)

```bash
# Requires .env with API keys
docker compose up --build
```

- API: http://localhost:8000
- Dashboard: http://localhost:3000

Note: Playwright scrapers (Reuters/Bloomberg) are not configured in the API container image. Use local Python env for full scrape support.

## Project Structure

```
src/backend/     # Python pipeline + FastAPI
src/frontend/    # Next.js dashboard
tests/           # unit + integration tests
data/            # SQLite (gitignored)
docs/            # specs + journals
plans/           # implementation plans
```

## Development Status

- [x] Phase 01 — Core foundation
- [x] Phase 02 — Data ingestion
- [x] Phase 03 — Gemini AI layer
- [x] Phase 04 — Dashboard
- [x] Phase 05 — Testing & ops

## Post-MVP Ideas

- Telegram/email alerts on high-impact news
- LSTM/ARIMA technical scoring alongside Gemini
- PDF report ingestion (Goldman, WGC)
