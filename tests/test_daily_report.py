"""Tests for daily report model mapping."""

from src.backend.core.ai_models import DailyGoldReport, ReportHorizonForecast


def test_daily_report_maps_to_forecast_result():
    horizon = ReportHorizonForecast(
        trend="up",
        confidence=70,
        reasoning="USD yếu hỗ trợ giá $XAU tăng.",
    )
    report = DailyGoldReport(
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

    forecast = report.to_forecast_result()
    assert forecast.day.trend == "up"
    assert "$" not in forecast.day.reasoning
