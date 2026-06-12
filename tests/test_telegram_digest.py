"""Tests for Telegram digest formatting."""

from src.backend.adapters.telegram_client import split_telegram_message
from src.backend.core.ai_models import DailyGoldReport, ReportHorizonForecast
from src.backend.services.telegram_digest import format_daily_digest


def _sample_report() -> DailyGoldReport:
    horizon = ReportHorizonForecast(
        trend="sideways",
        confidence=55,
        reasoning="Thị trường đi ngang do DXY ổn định.",
    )
    return DailyGoldReport(
        title="Báo cáo vàng 12/06",
        executive_summary="Vàng đi ngang trong ngắn hạn.",
        news_rationale="Theo Kitco, vàng giữ trên 4.200 do rủi ro Hormuz.",
        international_analysis="XAU chịu áp lực từ USD mạnh.",
        domestic_analysis="SJC theo đà thế giới, thanh khoản ổn.",
        international_trend="down",
        domestic_trend="sideways",
        international_price_outlook="Xu hướng giảm nhẹ trong tuần.",
        domestic_price_outlook="Giá trong nước đi ngang, biên độ hẹp.",
        confidence=60,
        key_drivers=["DXY mạnh", "Lãi suất cao"],
        risks=["Biến động địa chính trị"],
        day=horizon,
        week=horizon,
        month=horizon,
        quarter=horizon,
    )


def test_format_daily_digest_includes_vietnamese_sections(monkeypatch):
    monkeypatch.setattr(
        "src.backend.services.telegram_digest.get_latest_macro",
        lambda: {"gold_spot": 4189.0, "dxy": 120.0, "us10y": 4.5},
    )
    body = format_daily_digest(report=_sample_report())

    assert "Báo cáo vàng" in body
    assert "Quốc tế" in body
    assert "trong nước" in body
    assert "Cơ sở từ tin tức" in body
    assert "Kitco" in body
    assert "Tin tóm tắt hôm nay" not in body


def test_split_telegram_message_on_long_text():
    text = "A" * 5000
    chunks = split_telegram_message(text, limit=2000)
    assert len(chunks) >= 3
    assert all(len(chunk) <= 2000 for chunk in chunks)
