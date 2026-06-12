"""Format and send the latest daily forecast report via Telegram."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.backend.adapters.telegram_client import (
    TelegramClient,
    TelegramClientError,
    split_telegram_message,
)
from src.backend.core.ai_models import DailyGoldReport, Trend
from src.backend.core.database import get_latest_macro
from src.backend.services.daily_report import ensure_daily_report, load_latest_daily_report

logger = logging.getLogger(__name__)

TREND_VI: dict[Trend, str] = {
    "up": "Tăng",
    "down": "Giảm",
    "sideways": "Đi ngang",
}

@dataclass
class TelegramDigestResult:
    sent: bool = False
    message_count: int = 0
    message: str = ""


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_daily_digest(
    *,
    report: DailyGoldReport | None = None,
) -> str:
    macro = get_latest_macro() or {}
    report = report or load_latest_daily_report()

    lines: list[str] = [
        "<b>📊 GoldForecaster — Báo cáo forecast</b>",
        "",
        "<b>Ảnh macro</b>",
        f"• Vàng thế giới: {_fmt_spot(macro.get('gold_spot'))}",
        f"• DXY: {_fmt_num(macro.get('dxy'))}",
        f"• US 10Y: {_fmt_num(macro.get('us10y'))}%",
    ]

    if report:
        lines.extend(
            [
                "",
                f"<b>📋 { _escape_html(report.title) }</b>",
                "",
                "<b>Tóm tắt điều hành</b>",
                _escape_html(report.executive_summary),
                "",
                "<b>📰 Cơ sở từ tin tức hôm nay</b>",
                _escape_html(report.news_rationale),
                "",
                f"<b>🌍 Quốc tế (XAU/USD)</b> — {TREND_VI[report.international_trend]}",
                _escape_html(report.international_analysis),
                "",
                f"<b>Dự báo giá quốc tế:</b> {_escape_html(report.international_price_outlook)}",
                "",
                f"<b>🇻🇳 Vàng trong nước (SJC/9999)</b> — {TREND_VI[report.domestic_trend]}",
                _escape_html(report.domestic_analysis),
                "",
                f"<b>Dự báo giá trong nước:</b> {_escape_html(report.domestic_price_outlook)}",
                "",
                f"<b>Độ tin cậy:</b> {report.confidence}%",
                "",
                "<b>Yếu tố chính</b>",
                *_bullet_lines(report.key_drivers),
                "",
                "<b>Rủi ro</b>",
                *_bullet_lines(report.risks),
                "",
                "<b>Khung thời gian</b>",
                *_horizon_lines("Ngày", report.day),
                *_horizon_lines("Tuần", report.week),
                *_horizon_lines("Tháng", report.month),
                *_horizon_lines("Quý", report.quarter),
            ]
        )
    else:
        lines.extend(["", "<i>Chưa có báo cáo forecast chi tiết.</i>"])

    return "\n".join(lines)


def _bullet_lines(items: list[str]) -> list[str]:
    return [f"• {_escape_html(item)}" for item in items]


def _horizon_lines(label: str, horizon) -> list[str]:
    return [
        "",
        f"<b>• {label}:</b> {TREND_VI[horizon.trend]} ({horizon.confidence}%)",
        _escape_html(horizon.reasoning),
    ]


def _fmt_spot(value: object) -> str:
    if value is None:
        return "N/A"
    spot = float(value)
    if spot >= 800:
        return f"${spot:,.2f}/oz"
    return "N/A"


def _fmt_num(value: object) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):,.2f}"


def send_daily_digest(*, ensure_report: bool = True) -> TelegramDigestResult:
    try:
        client = TelegramClient()
    except TelegramClientError as exc:
        return TelegramDigestResult(message=str(exc))

    if ensure_report:
        gen = ensure_daily_report()
        if not gen.saved:
            return TelegramDigestResult(message=gen.message)

    body = format_daily_digest()
    chunks = split_telegram_message(body)
    try:
        count = client.send_messages(chunks)
    except TelegramClientError as exc:
        return TelegramDigestResult(message=f"Gửi Telegram thất bại: {exc}")

    return TelegramDigestResult(
        sent=True,
        message_count=count,
        message=f"Đã gửi {count} tin nhắn Telegram.",
    )
