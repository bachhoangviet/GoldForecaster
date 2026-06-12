---
title: "GoldForecaster MVP Implementation"
description: "End-to-end gold forecasting pipeline: scrape 5 sources, Gemini Flash AI, SQLite, Next.js dashboard — local MVP"
status: completed
priority: P1
effort: 320h
branch: main
tags: [feature, backend, frontend, api, ai, scraper]
blockedBy: []
blocks: []
created: 2026-06-10
---

# GoldForecaster MVP Implementation Plan

## Overview

Triển khai Modular Monolith theo PRD/Architecture: Python backend (scrapers, Gemini, SQLite WAL), FastAPI REST (gap-fill), Next.js dashboard, CLI `main.py`. Approach A — docs-as-written. Budget $0 → Gemini Flash only.

**Brainstorm ref:** [260610-goldforecaster-brainstorm](../reports/260610-goldforecaster-brainstorm.md)

## Cross-Plan Dependencies

None — greenfield project, no existing plans.

## Phases

| Phase | Name | Status | Effort |
|-------|------|--------|--------|
| 1 | [Core Foundation](./phase-01-core-foundation.md) | Completed | 40h |
| 2 | [Data Ingestion Pipeline](./phase-02-data-ingestion.md) | Completed | 80h |
| 3 | [Gemini AI Layer](./phase-03-gemini-ai-layer.md) | Completed | 60h |
| 4 | [Dashboard Frontend](./phase-04-dashboard-frontend.md) | Completed | 80h |
| 5 | [Testing & Operations](./phase-05-testing-ops.md) | Completed | 60h |

## Dependencies

- Python 3.10+, Node.js 18+
- `GEMINI_API_KEY` (Google AI Studio free tier)
- `FRED_API_KEY` (free, stlouisfed.org)
- Playwright browsers (`playwright install chromium`)

## Unresolved (Track During Implementation)

- Exact Gemini model slug at implementation time (use latest Flash free in AI Studio)
- SPDR holdings: SSGA scrape vs yfinance — validate in Phase 2
- Reuters/Bloomberg selectors — fragile, expect weekly maintenance

## Cook Handoff

```
/ck:cook plans/260610-goldforecaster-mvp
```
