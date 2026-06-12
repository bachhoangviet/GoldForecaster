# Phase 01 — Core Foundation (Epic 1)

**Priority:** P1 | **Status:** Completed | **Effort:** ~40h

## Context Links

- PRD Epic 1: `docs/2_prd.md`
- Architecture: `docs/3_architecture.md`
- Brainstorm: `plans/reports/260610-goldforecaster-brainstorm.md`

## Overview

Khởi tạo monorepo, Python venv, env security, SQLite WAL, Gemini client ping, FastAPI skeleton, CLI `main.py`.

## Key Insights

- Project greenfield — no `src/` yet
- `docs/development-rules.md` không tồn tại — follow PEP 8 + PRD conventions
- FastAPI không có trong architecture doc nhưng bắt buộc cho Next.js ↔ Python

## Requirements

**Functional**
- Monorepo dirs: `src/backend/{core,services,adapters,api}/`, `src/frontend/`, `tests/`, `docs/`
- `.env` + `.env.example` với `GEMINI_API_KEY`, `FRED_API_KEY`
- `gemini_client.py` ping test
- `database.py` SQLite WAL + migrations/init schema
- `main.py` CLI: `--test-ai`, `--run-scraper`, `--show-data` (stubs OK for scraper/show)
- FastAPI app với `/health`, CORS for localhost:3000

**Non-Functional**
- No hardcoded secrets
- Graceful error messages on CLI

## Architecture

```
goldforecaster/
├── main.py
├── requirements.txt
├── .env.example
├── src/
│   ├── backend/
│   │   ├── core/
│   │   │   ├── config.py      # pydantic-settings or dotenv loader
│   │   │   └── database.py    # SQLite WAL, connection pool
│   │   ├── adapters/
│   │   │   └── gemini_client.py
│   │   └── api/
│   │       ├── app.py         # FastAPI factory
│   │       └── routes/
│   │           └── health.py
│   └── frontend/              # Phase 4 — placeholder package.json
├── tests/
│   └── test_gemini_client.py
└── docs/
```

## Related Code Files

| Action | Path |
|--------|------|
| Create | `main.py` |
| Create | `requirements.txt` |
| Create | `src/backend/core/config.py` |
| Create | `src/backend/core/database.py` |
| Create | `src/backend/adapters/gemini_client.py` |
| Create | `src/backend/api/app.py` |
| Create | `.env.example`, `.gitignore` |
| Create | `README.md` (setup one-liner) |

## Implementation Steps

1. **Scaffold monorepo** — dirs per PRD Story 1.1
2. **requirements.txt** — `python-dotenv`, `google-genai`, `fastapi`, `uvicorn`, `click`, `pydantic-settings`, `httpx`, `pytest`
3. **config.py** — load env, validate required keys on startup
4. **database.py** — enable WAL: `PRAGMA journal_mode=WAL`; init tables (articles, macro_snapshots, forecasts, scrape_runs)
5. **gemini_client.py** — SDK wrapper, `ping()` sends short prompt, catches network/auth/rate-limit errors
6. **main.py** — click/argparse commands wiring to modules
7. **FastAPI** — `uvicorn src.backend.api.app:app --reload --port 8000`
8. **Tests** — mock Gemini for unit test; integration test skipped without key
9. **README** — `python -m venv .venv`, `pip install -r requirements.txt`, copy `.env.example`

## Todo List

- [x] Monorepo structure
- [x] Env + gitignore
- [x] SQLite schema + WAL
- [x] Gemini client + `--test-ai`
- [x] FastAPI health endpoint
- [x] CLI shell stubs
- [x] README setup guide

## Success Criteria

- `python main.py --test-ai` → success message with model response snippet
- `curl localhost:8000/health` → `{"status":"ok"}`
- `.env` not in git
- Tables created on first run

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Wrong Gemini SDK package | Use `google-genai` per architecture doc |
| SQLite concurrent access | WAL + document single-writer for scrapers |

## Security Considerations

- `.env` in `.gitignore`
- No API keys in frontend
- CORS restricted to `localhost:3000` dev

## Next Steps

→ Phase 02: wire scrapers into CLI `--run-scraper`, persist to SQLite
