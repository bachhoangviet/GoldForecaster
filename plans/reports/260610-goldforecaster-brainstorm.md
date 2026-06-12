# Brainstorm Report: GoldForecaster MVP

**Date:** 2026-06-10  
**Status:** Approved — Approach A (Docs-as-written)  
**Sources:** `docs/1_project_brief.md`, `docs/2_prd.md`, `docs/3_architecture.md`

---

## Problem Statement

GoldForecaster cần pipeline end-to-end: thu thập tin vĩ mô + số liệu cứng → tóm tắt/gán nhãn bằng Gemini → dự báo xu hướng 4 khung thời gian → hiển thị trên Dashboard Next.js. MVP mục tiêu 1-2 tháng, chạy local, ngân sách API $0.

## User Constraints (Confirmed)

| Dimension | Choice |
|-----------|--------|
| Priority | Cân bằng pipeline + dashboard MVP |
| Data sources | Scrape đủ 5 nguồn (Kitco, Reuters, Bloomberg, CNBC, FED) |
| Budget | Free tier only |
| Deployment | Local-only |

## Brutal Honesty — Constraint Tensions

1. **Scrape-hard + $0** = rủi ro cao. Reuters/Bloomberg chống bot mạnh; không proxy trả phí → scraper sẽ gãy thường xuyên, cần bảo trì DOM selector hằng tuần.
2. **Gemini free tier** (~10-15 RPM, ~1500 RPD/project) đủ cho MVP nếu: chỉ dùng **Flash**, batch summarize, cache SQLite, forecast chỉ khi có tin mới (đúng PRD).
3. **"Advanced/Ultra" trong PRD** không khả thi free tier — **chỉ Flash** cho cả summarize lẫn forecast.
4. **Thiếu trong architecture doc:** REST API layer Python↔Next.js, SQLite schema, nguồn giá vàng/SPDR cụ thể. Plan bổ sung tối thiểu cần thiết.
5. **Legal/ToS:** scrape Bloomberg/Reuters có thể vi phạm điều khoản — chấp nhận cho dev/demo local, không production công khai.

## Approaches Evaluated

### A — Docs-as-written ✅ SELECTED

Modular Monolith Python + Next.js monorepo, SQLite WAL, adapter scrapers (BS4 + Playwright), Gemini Flash only, CLI `main.py`, dashboard theo PRD.

**Pros:** Khớp docs 100%, một codebase, dễ debug local  
**Cons:** Scraper fragility, không scale ngang, thiếu API layer trong docs (cần bổ sung FastAPI mỏng)

### B — Resilient Balanced (khuyến nghị ban đầu)

Giống A + circuit breaker per source, graceful degradation UI, batch AI queue.

**Pros:** UX ổn hơn khi nguồn chết  
**Cons:** Thêm complexity, user không chọn

### C — Staged Balanced

Dashboard sớm với 2 nguồn, mở rộng sau.

**Pros:** Ship nhanh hơn  
**Cons:** Lệch PRD scrape 5 nguồn

## Final Recommended Solution (Approach A)

### Architecture

```
┌─────────────┐     REST      ┌──────────────────────────────────┐
│  Next.js    │ ◄──────────► │  FastAPI (thin, docs gap-fill)    │
│  Dashboard  │   :8000      │  src/backend/api/                 │
└─────────────┘              └──────────┬───────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
            ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
            │  Scrapers    │   │  Gemini      │   │  SQLite WAL  │
            │  adapters/   │   │  services/   │   │  core/db     │
            └──────────────┘   └──────────────┘   └──────────────┘
                    ▲
            ┌───────┴────────┐
            │ APScheduler    │  cron local
            │ main.py CLI    │
            └────────────────┘
```

### Key Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| AI model | `gemini-2.0-flash` or latest Flash free | Pro/Advanced không free |
| Forecast output | Structured JSON: trend + confidence only | Tránh hallucination giá tuyệt đối |
| Macro data | FRED API (DGS10, DTWEXBGS/DXY proxy) free key | Chính thống, ổn định |
| Gold price | Kitco scrape + cache | Đã trong scope |
| SPDR GLD | Scrape SSGA holdings page hoặc yfinance fallback | Free, brittle → retry |
| Backend↔Frontend | FastAPI REST | Docs thiếu nhưng bắt buộc cho Next.js |
| Scheduler | APScheduler in-process | Local MVP, không cần Celery |

### SQLite Schema (Sketch)

- `articles` — raw + summary + sentiment + source + scraped_at
- `macro_snapshots` — dxy, us10y, spdr_holdings, gold_spot, recorded_at
- `forecasts` — horizon (day/week/month/quarter), trend, confidence, reasoning, created_at
- `scrape_runs` — source, status, error, duration (observability)

### Build Order (Balanced, 8 tuần)

| Week | Focus |
|------|-------|
| 1-2 | Epic 1: monorepo, env, Gemini ping, SQLite, FastAPI skeleton |
| 3-4 | Epic 2: Kitco/FED/CNBC scrapers + FRED macro |
| 5 | Epic 2 cont: Reuters/Bloomberg Playwright + Epic 3 summarize |
| 6 | Epic 3: predictor + structured output + CLI full pipeline |
| 7-8 | Epic 4 dashboard + Epic 5 integration tests |

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Bloomberg/Reuters block | High | Playwright stealth, 4x/day, retry 3x, log `scrape_runs` |
| Gemini 429 | Medium | Queue, cache, dedupe articles by URL hash |
| LLM hallucination | Medium | JSON schema, no absolute price in prompt |
| SQLite lock | Low | WAL mode + single writer pattern |
| DOM change | High | `--run-scraper` dry-run CLI, per-adapter tests |

## Success Metrics

- [ ] `--test-ai` pass
- [ ] `--run-scraper` extract ≥1 article/source (5 sources configured)
- [ ] `--show-data` shows macro + summaries
- [ ] Forecast JSON valid 4 horizons after new articles ingested
- [ ] Dashboard loads chart + news + forecast widget from API
- [ ] Full scrape cycle < 5 min (NFR)
- [ ] Zero hardcoded API keys

## Next Steps

→ Implementation plan: `plans/260610-goldforecaster-mvp/plan.md`  
→ Cook command: `/ck:cook plans/260610-goldforecaster-mvp`
