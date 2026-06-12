"""Tests for market data adapters."""

import asyncio
from unittest.mock import patch

import pytest

from src.backend.adapters.market_api import (
    FredApiError,
    _parse_gold_price,
    fetch_fred_macro,
)
from src.backend.core.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_parse_gold_price_from_bid_selector():
    html = '<html><body><div id="sp-bid">2,345.60</div></body></html>'
    assert _parse_gold_price(html) == 2345.60


def test_parse_gold_price_from_text_fallback():
    html = "<html><body>Gold Spot $1,980.25 updated now</body></html>"
    assert _parse_gold_price(html) == 1980.25


def test_fetch_fred_macro_missing_key(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(FredApiError, match="FRED_API_KEY"):
        asyncio.run(fetch_fred_macro())


def test_fetch_fred_macro_success(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "test-fred-key")
    get_settings.cache_clear()

    def fake_latest(series_id: str, api_key: str) -> float:
        assert api_key == "test-fred-key"
        return 4.25 if series_id == "DGS10" else 121.5

    with patch("src.backend.adapters.market_api._fred_latest", side_effect=fake_latest):
        dxy, us10y = asyncio.run(fetch_fred_macro())

    assert us10y == 4.25
    assert dxy == 121.5
