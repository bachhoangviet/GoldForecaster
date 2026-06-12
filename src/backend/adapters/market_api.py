"""Market data adapters: FRED macro series, Kitco gold spot, SPDR holdings."""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
import yfinance as yf
from bs4 import BeautifulSoup

from src.backend.adapters.scraper_utils import fetch_html, retry_request
from src.backend.core.config import get_settings
from src.backend.core.models import MacroSnapshot, ScrapeRunRecord, ScrapeStatus

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
KITCO_GOLD_URL = "https://www.kitco.com/charts/livegold.html"
SPDR_URL = "https://www.spdrgoldshares.com/"


class FredApiError(Exception):
    """FRED API request failed."""


@retry_request()
def _fred_latest(series_id: str, api_key: str) -> float | None:
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }
    response = httpx.get(FRED_BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    observations: list[dict[str, Any]] = payload.get("observations", [])
    if not observations:
        return None

    value = observations[0].get("value")
    if value in (None, ".", ""):
        return None
    return float(value)


async def fetch_fred_macro() -> tuple[float | None, float | None]:
    settings = get_settings()
    if not settings.fred_api_key or settings.fred_api_key == "your_key_here":
        raise FredApiError(
            "FRED_API_KEY is not configured. Copy .env.example to .env and add your key."
        )

    us10y, dxy = await asyncio.gather(
        asyncio.to_thread(_fred_latest, "DGS10", settings.fred_api_key),
        asyncio.to_thread(_fred_latest, "DTWEXBGS", settings.fred_api_key),
    )
    return dxy, us10y


def _is_plausible_gold_spot(value: float | None) -> bool:
    return value is not None and 800 <= value <= 10_000


def _parse_gold_price(html: str) -> float | None:
    soup = BeautifulSoup(html, "html.parser")

    kitco_mid = re.search(
        r'"high"\s*:\s*([\d.]+)\s*,\s*"low"\s*:\s*([\d.]+)\s*,\s*"mid"\s*:\s*([\d.]+)',
        html,
    )
    if kitco_mid:
        mid = _extract_number(kitco_mid.group(3))
        if _is_plausible_gold_spot(mid):
            return mid

    selectors = [
        "#sp-bid",
        "#lblSPOT",
        ".price-bid",
        "[data-test='price-bid']",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            value = _extract_number(node.get_text(" ", strip=True))
            if _is_plausible_gold_spot(value):
                return value

    text = soup.get_text(" ", strip=True)
    match = re.search(r"Gold.*?\$\s*([\d,]+\.?\d*)", text, re.IGNORECASE)
    if match:
        value = _extract_number(match.group(1))
        if _is_plausible_gold_spot(value):
            return value

    return None


def _fetch_yfinance_gold_spot() -> float | None:
    try:
        ticker = yf.Ticker("GC=F")
        fast_info = getattr(ticker, "fast_info", None)
        if fast_info is not None:
            last_price = getattr(fast_info, "last_price", None)
            if _is_plausible_gold_spot(last_price):
                return float(last_price)
        info = ticker.info
        for key in ("regularMarketPrice", "previousClose"):
            candidate = info.get(key)
            if _is_plausible_gold_spot(candidate):
                return float(candidate)
    except Exception:
        return None
    return None


def _extract_number(raw: str) -> float | None:
    cleaned = raw.replace(",", "").replace("$", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


@retry_request()
def fetch_kitco_gold_spot() -> float | None:
    html = fetch_html(KITCO_GOLD_URL)
    price = _parse_gold_price(html)
    if _is_plausible_gold_spot(price):
        return price
    return _fetch_yfinance_gold_spot()


@retry_request()
def fetch_spdr_holdings() -> float | None:
    try:
        html = fetch_html(SPDR_URL)
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        match = re.search(
            r"Total Gold.*?([\d,]+\.?\d*)\s*(?:tonnes|metric tons|tons)",
            text,
            re.IGNORECASE,
        )
        if match:
            return _extract_number(match.group(1))
    except Exception:
        pass

    try:
        ticker = yf.Ticker("GLD")
        fast_info = getattr(ticker, "fast_info", None)
        if fast_info and hasattr(fast_info, "last_price"):
            shares = getattr(fast_info, "shares", None)
            if shares:
                # Approximate tonnes proxy from outstanding shares (MVP fallback).
                return float(shares) / 1_000_000
    except Exception:
        pass

    info = yf.Ticker("GLD").info
    total_assets = info.get("totalAssets")
    if total_assets:
        return float(total_assets) / 1_000_000_000
    return None


async def fetch_macro_snapshot() -> MacroSnapshot:
    dxy, us10y = await fetch_fred_macro()
    gold_spot, spdr_holdings = await asyncio.gather(
        asyncio.to_thread(fetch_kitco_gold_spot),
        asyncio.to_thread(fetch_spdr_holdings),
    )
    return MacroSnapshot(
        dxy=dxy,
        us10y=us10y,
        spdr_holdings=spdr_holdings,
        gold_spot=gold_spot,
    )


async def run_macro_ingestion() -> tuple[ScrapeRunRecord, MacroSnapshot | None]:
    import time

    started = time.perf_counter()
    try:
        snapshot = await fetch_macro_snapshot()
        duration_ms = int((time.perf_counter() - started) * 1000)
        has_values = any(
            value is not None
            for value in (
                snapshot.dxy,
                snapshot.us10y,
                snapshot.spdr_holdings,
                snapshot.gold_spot,
            )
        )
        status = ScrapeStatus.SUCCESS if has_values else ScrapeStatus.PARTIAL
        record = ScrapeRunRecord(
            source="macro",
            status=status,
            duration_ms=duration_ms,
            error=None if has_values else "No macro values parsed",
        )
        return record, snapshot
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ScrapeRunRecord(
            source="macro",
            status=ScrapeStatus.FAILED,
            duration_ms=duration_ms,
            error=str(exc),
        ), None
