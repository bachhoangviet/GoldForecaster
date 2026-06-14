"""Tests for daily report model mapping."""

from unittest.mock import patch

from src.backend.core.ai_models import (
    DailyGoldReport,
    HorizonForecast,
    ReportHorizonForecast,
    sanitize_reasoning_for_forecast,
)


def _sample_report(*, reasoning: str) -> DailyGoldReport:
    horizon = ReportHorizonForecast(
        trend="up",
        confidence=70,
        reasoning=reasoning,
    )
    return DailyGoldReport(
        title="Test",
        executive_summary="Tóm tắt",
        news_rationale="Kitco báo USD mạnh; CNBC ghi nhận dòng tiền vào ETF.",
        international_analysis="Quốc tế",
        domestic_analysis="Trong nước",
        international_trend="up",
        domestic_trend="up",
        international_price_outlook="Tăng nhẹ",
        domestic_price_outlook="Theo đà",
        confidence=65,
        key_drivers=["USD"],
        risks=["CPI"],
        day=horizon,
        week=horizon,
        month=horizon,
        quarter=horizon,
    )


def test_daily_report_maps_to_forecast_result():
    report = _sample_report(reasoning="USD yếu hỗ trợ giá $XAU tăng.")

    forecast = report.to_forecast_result()
    assert forecast.day.trend == "up"
    assert "$" not in forecast.day.reasoning


def test_sanitize_strips_usd_oz():
    raw = "Trong ngắn hạn 24 giờ, giá duy trì quanh 4.200 USD/oz, hạn đà giảm sâu."
    cleaned = sanitize_reasoning_for_forecast(raw)

    HorizonForecast(trend="up", confidence=70, reasoning=cleaned)
    assert "usd/oz" not in cleaned.lower()
    assert "$" not in cleaned


def test_to_forecast_result_with_price_leak():
    reasoning = (
        "Trong phiên hôm nay, giá vàng thế giới duy trì trên 4.200 USD/oz "
        "nhờ USD yếu và kỳ vọng FED cắt lãi suất."
    )
    report = _sample_report(reasoning=reasoning)

    forecast = report.to_forecast_result()

    assert forecast.day.trend == "up"
    assert "usd/oz" not in forecast.day.reasoning.lower()


def test_to_forecast_result_uses_fallback_when_sanitize_insufficient():
    report = _sample_report(reasoning="Gold will reach $5000 on strong flows.")

    with patch(
        "src.backend.core.ai_models.sanitize_reasoning_for_forecast",
        return_value="Gold will reach $5000 on strong flows.",
    ):
        forecast = report.to_forecast_result()

    assert forecast.day.reasoning == (
        "Xu hướng dựa trên driver vĩ mô và sentiment tin tức trong ngày."
    )
