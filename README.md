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
| `python main.py --run-daily-job` | Full daily: ingest → summarize → báo cáo VI → Telegram |
| `python main.py --daily-report` | Generate detailed Vietnamese forecast report only |
| `python main.py --send-telegram` | Send latest forecast report to Telegram |

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
| `TELEGRAM_BOT_TOKEN` | Yes (Telegram) | Bot token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Yes (Telegram) | Your chat id (`getUpdates` or [@userinfobot](https://t.me/userinfobot)) |
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

## Deploy daily job (GitHub Actions — free)

Chạy tự động **mỗi ngày 7:00 sáng giờ Việt Nam**, gửi báo cáo forecast qua Telegram. Không cần server 24/7.

### 1. Push repo lên GitHub (public)

Đảm bảo `.env` **không** được commit (đã có trong `.gitignore`).

### 2. Thêm Secrets

Repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Mô tả |
|--------|--------|
| `GEMINI_API_KEY` | Google AI Studio API key |
| `FRED_API_KEY` | FRED macro API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Chat id nhận báo cáo |

Optional **Variables** (tab Variables, không bắt buộc):

- `GEMINI_SUMMARIZE_MODELS` — ví dụ `gemini-3.1-flash-lite,gemma-4-26b,...`
- `GEMINI_FORECAST_MODELS` — ví dụ `gemini-3.5-flash,gemini-3.1-flash-lite,...`
- `GEMINI_REQUEST_DELAY_SECONDS` — mặc định `8`
- `SUMMARIZE_BATCH_LIMIT` — mặc định `100`

### 3. Bật workflow

Workflow: [`.github/workflows/daily-job.yml`](.github/workflows/daily-job.yml)

- Lịch: `0 0 * * *` UTC = **07:00 Asia/Ho_Chi_Minh**
- GitHub có thể trễ 5–15 phút — bình thường

### 4. Test thủ công

1. Tab **Actions** → **Daily Gold Forecast**
2. **Run workflow** → **Run workflow**
3. Mở job run → xem log; kiểm tra Telegram

### 5. Lưu ý vận hành

- Repo cần commit ít nhất 1 lần / 60 ngày để GitHub không tạm dừng schedule
- Reuters/Bloomberg có thể fail trên IP datacenter — Kitco/CNBC/FED vẫn đủ cho báo cáo
- Không lưu SQLite giữa các lần chạy (mỗi lần scrape + summarize mới từ đầu)
- **Không** đưa API key vào code hoặc commit history

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
