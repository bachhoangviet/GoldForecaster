"""Telegram Bot API adapter for daily digest delivery."""

from __future__ import annotations

import logging

import httpx

from src.backend.core.config import get_settings

logger = logging.getLogger(__name__)

TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_SAFE_CHUNK = 3800


class TelegramClientError(Exception):
    """Telegram delivery failed."""


class TelegramClient:
    def __init__(
        self,
        *,
        bot_token: str | None = None,
        chat_id: str | None = None,
    ) -> None:
        settings = get_settings()
        self.bot_token = bot_token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id

        if not self.bot_token or self.bot_token == "your_bot_token_here":
            raise TelegramClientError(
                "TELEGRAM_BOT_TOKEN chưa cấu hình. Tạo bot qua @BotFather và thêm vào .env."
            )
        if not self.chat_id or self.chat_id == "your_chat_id_here":
            raise TelegramClientError(
                "TELEGRAM_CHAT_ID chưa cấu hình. Lấy chat id từ @userinfobot hoặc getUpdates."
            )

    def send_message(self, text: str, *, parse_mode: str | None = "HTML") -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload: dict[str, object] = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        response = httpx.post(url, json=payload, timeout=30)
        if response.status_code != 200:
            raise TelegramClientError(
                f"Telegram API error {response.status_code}: {response.text[:300]}"
            )

    def send_messages(self, chunks: list[str], *, parse_mode: str = "HTML") -> int:
        sent = 0
        for index, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            try:
                self.send_message(chunk, parse_mode=parse_mode)
                sent += 1
            except TelegramClientError:
                logger.warning("Telegram HTML failed for chunk %d, retry plain text", index + 1)
                self.send_message(_strip_html(chunk), parse_mode=None)  # type: ignore[arg-type]
                sent += 1
        return sent


def _strip_html(text: str) -> str:
    return (
        text.replace("<b>", "")
        .replace("</b>", "")
        .replace("<i>", "")
        .replace("</i>", "")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )


def split_telegram_message(text: str, limit: int = TELEGRAM_SAFE_CHUNK) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        block = paragraph if not current else f"\n\n{paragraph}"
        if len(current) + len(block) <= limit:
            current += block
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= limit:
            current = paragraph
        else:
            for i in range(0, len(paragraph), limit):
                chunks.append(paragraph[i : i + limit])
            current = ""
    if current:
        chunks.append(current)
    return chunks
