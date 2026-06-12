"""Shared scraping utilities: retries, user agents, HTML cleanup."""

from __future__ import annotations

import random
import re
import time
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

import requests
from bs4 import BeautifulSoup

P = ParamSpec("P")
R = TypeVar("R")

USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
]

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def default_headers() -> dict[str, str]:
    return {
        "User-Agent": random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


def retry_request(
    max_retries: int = MAX_RETRIES,
    backoff_seconds: int = RETRY_BACKOFF_SECONDS,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry decorator for network-facing fetch helpers."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, TimeoutError, OSError) as exc:
                    last_error = exc
                    if attempt < max_retries:
                        time.sleep(backoff_seconds)
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator


@retry_request()
def fetch_html(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    response = requests.get(url, headers=default_headers(), timeout=timeout)
    response.raise_for_status()
    return response.text


def strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text)


def normalize_url(base_url: str, href: str) -> str | None:
    if not href or href.startswith("#") or href.startswith("javascript:"):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return href.split("#")[0]
    if href.startswith("//"):
        return f"https:{href.split('#')[0]}"
    if href.startswith("/"):
        from urllib.parse import urljoin

        return urljoin(base_url, href.split("#")[0])
    return None


def truncate_text(text: str, max_length: int = 4000) -> str:
    cleaned = text.strip()
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3] + "..."
