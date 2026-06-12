# Phase 04 — Dashboard Frontend (Epic 4)

**Priority:** P1 | **Status:** Completed | **Effort:** ~80h

## Context Links

- PRD Epic 4 + UX: `docs/2_prd.md` § User Interaction
- Depends on: Phase 01 (FastAPI), Phase 03 (forecast data)

## Overview

Next.js App Router + Tailwind dashboard: gold chart, AI news feed, multi-horizon forecast widget. Dark finance theme (Deep Blue/Slate + Gold accent).

## Key Insights

- Frontend reads via FastAPI REST — never direct SQLite
- "Real-time" chart = poll every 60s or SWR revalidate (local MVP, no WebSocket needed)
- Chart library: `lightweight-charts` (TradingView) or `recharts` — prefer lightweight-charts for finance UX
- No auth for local MVP

## Requirements

**Functional**
- API routes (FastAPI):
  - `GET /api/macro/latest` — DXY, US10Y, SPDR, gold_spot
  - `GET /api/macro/history?days=30` — gold price series for chart
  - `GET /api/news?sentiment=bullish` — summarized articles, filter optional
  - `GET /api/forecasts/latest` — 4 horizons
- Dashboard layout per PRD:
  - Top-left: gold price chart (line/candle)
  - Top-right: forecast widget with Day/Week/Month/Quarter tabs
  - Bottom: news table with sentiment color badges
- Sentiment filter: Bullish / Bearish / All
- Confidence bar per horizon (0-100%)
- Trend arrows: up/down/sideways

**Non-Functional**
- Responsive desktop-first
- Initial load < 3s local
- Graceful empty states when scraper hasn't run

## Architecture

```
src/frontend/                    # Next.js 14+ App Router
├── app/
│   ├── layout.tsx               # dark theme, fonts
│   ├── page.tsx                 # main dashboard
│   └── globals.css
├── components/
│   ├── gold-chart.tsx
│   ├── forecast-widget.tsx
│   ├── news-feed.tsx
│   └── ui/                      # shadcn-style primitives
├── lib/
│   └── api.ts                   # fetch wrapper → localhost:8000
└── package.json
```

**Color tokens:**
- Background: `slate-950` / `blue-950`
- Accent gold: `amber-500`
- Bullish: `emerald-500`, Bearish: `rose-500`, Neutral: `slate-400`

## Related Code Files

| Action | Path |
|--------|------|
| Create | `src/frontend/` Next.js app |
| Create | `src/backend/api/routes/macro.py` |
| Create | `src/backend/api/routes/news.py` |
| Create | `src/backend/api/routes/forecasts.py` |
| Modify | `src/backend/api/app.py` — register routers |
| Create | `src/frontend/components/*.tsx` |
| Create | `src/frontend/lib/api.ts` |

## Implementation Steps

1. **Scaffold Next.js** — `npx create-next-app@latest` in `src/frontend`, TypeScript, Tailwind, App Router
2. **FastAPI routes** — query SQLite read-only, Pydantic response models
3. **api.ts** — `API_BASE=http://localhost:8000`, typed fetch helpers
4. **layout.tsx** — dark theme, header "GoldForecaster", last updated timestamp
5. **gold-chart.tsx** — fetch history, render line chart with gold color
6. **forecast-widget.tsx** — tabs 4 horizons, arrow + confidence Progress bar + reasoning expand
7. **news-feed.tsx** — table/cards, sentiment badge, source, time ago
8. **Sentiment filter** — client-side or query param
9. **Empty/loading states** — skeleton UI
10. **README** — `npm run dev` frontend + `uvicorn` backend concurrently
11. **Optional:** `concurrently` script at monorepo root

## Todo List

- [x] Next.js scaffold + Tailwind theme
- [x] FastAPI read endpoints
- [x] Gold chart component
- [x] Forecast widget + tabs
- [x] News feed + filter
- [x] API client types
- [x] Empty/loading states
- [x] Dev run documentation

## Success Criteria

- Dashboard at `localhost:3000` shows real data after `--run-pipeline`
- Tab switch shows correct horizon forecast
- News filter by sentiment works
- Chart renders ≥7 days gold history
- UI matches dark finance aesthetic from PRD

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| CORS issues | FastAPI CORSMiddleware configured Phase 01 |
| Stale data | Display `last_updated` from API |
| No data on first open | Onboarding empty state with CLI instructions |

## Security Considerations

- No secrets in `NEXT_PUBLIC_*`
- API read-only endpoints for MVP

## Next Steps

→ Phase 05: integration tests, cron reliability, README polish
