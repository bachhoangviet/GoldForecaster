"""News scraper adapters for Kitco, FED, CNBC, Reuters, and Bloomberg."""

from __future__ import annotations

import asyncio
import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.backend.adapters.scraper_utils import (
    fetch_html,
    normalize_url,
    random_user_agent,
    strip_html,
    truncate_text,
)
from src.backend.core.models import RawArticle, ScrapeRunRecord, ScrapeStatus

MAX_ARTICLES_PER_SOURCE = 10


class NewsScraper(ABC):
    source: str

    @abstractmethod
    async def fetch(self) -> list[RawArticle]:
        """Fetch and parse articles from the source."""

    def parse(self, html: str) -> list[RawArticle]:
        """Optional HTML parser hook for tests and static fixtures."""
        raise NotImplementedError(f"{self.source} does not implement parse()")


class KitcoNewsScraper(NewsScraper):
    source = "kitco"
    list_url = "https://www.kitco.com/news/"

    async def fetch(self) -> list[RawArticle]:
        html = await asyncio.to_thread(fetch_html, self.list_url)
        return self.parse(html)

    def parse(self, html: str) -> list[RawArticle]:
        soup = BeautifulSoup(html, "html.parser")
        articles: list[RawArticle] = []
        seen: set[str] = set()

        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "")
            url = normalize_url(self.list_url, href)
            if not url or "kitco.com" not in url or url in seen:
                continue
            if "/news/" not in url and "/opinion/" not in url:
                continue

            title = anchor.get_text(" ", strip=True)
            if len(title) < 12:
                continue

            seen.add(url)
            articles.append(
                RawArticle(
                    source=self.source,
                    url=url,
                    title=title,
                    body=title,
                    published_at=None,
                )
            )
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break

        return articles


class FedNewsScraper(NewsScraper):
    source = "fed"
    feed_url = "https://www.federalreserve.gov/feeds/press_all.xml"

    async def fetch(self) -> list[RawArticle]:
        xml_text = await asyncio.to_thread(fetch_html, self.feed_url)
        return self.parse(xml_text)

    def parse(self, html: str) -> list[RawArticle]:
        start = html.find("<?xml")
        if start == -1:
            start = html.find("<rss")
        if start == -1:
            raise ValueError("FED feed response does not contain XML payload")
        cleaned = html[start:].strip()
        root = ET.fromstring(cleaned)
        articles: list[RawArticle] = []

        for item in root.findall(".//item")[:MAX_ARTICLES_PER_SOURCE]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = strip_html(item.findtext("description") or "")
            pub_date = (item.findtext("pubDate") or "").strip() or None

            if not title or not link:
                continue

            articles.append(
                RawArticle(
                    source=self.source,
                    url=link,
                    title=title,
                    body=truncate_text(description or title),
                    published_at=pub_date,
                )
            )

        return articles


class CnbcNewsScraper(NewsScraper):
    source = "cnbc"
    list_url = "https://www.cnbc.com/gold/"

    async def fetch(self) -> list[RawArticle]:
        html = await asyncio.to_thread(fetch_html, self.list_url)
        return self.parse(html)

    def parse(self, html: str) -> list[RawArticle]:
        soup = BeautifulSoup(html, "html.parser")
        articles: list[RawArticle] = []
        seen: set[str] = set()

        selectors = [
            "a.Card-title",
            "a.LatestNews-headline",
            "div.Card-titleContainer a",
            "a[data-testid='Heading']",
        ]

        for selector in selectors:
            for anchor in soup.select(selector):
                href = anchor.get("href", "")
                url = normalize_url(self.list_url, href)
                if not url or "cnbc.com" not in url or url in seen:
                    continue

                title = anchor.get_text(" ", strip=True)
                if len(title) < 12:
                    continue

                seen.add(url)
                articles.append(
                    RawArticle(
                        source=self.source,
                        url=url,
                        title=title,
                        body=title,
                        published_at=None,
                    )
                )
                if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                    return articles

        return articles


class PlaywrightNewsScraper(NewsScraper):
    """Base Playwright scraper for anti-bot sources."""

    list_url: str
    link_pattern: str

    async def fetch(self) -> list[RawArticle]:
        from playwright.async_api import async_playwright

        articles: list[RawArticle] = []
        seen: set[str] = set()

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random_user_agent())
            page = await context.new_page()
            try:
                await page.goto(
                    self.list_url,
                    wait_until="domcontentloaded",
                    timeout=45_000,
                )
                await page.wait_for_timeout(2_000)
                anchors = await page.eval_on_selector_all(
                    "a[href]",
                    """elements => elements.map(el => ({
                        href: el.href,
                        text: (el.innerText || '').trim()
                    }))""",
                )
            finally:
                await context.close()
                await browser.close()

        host = urlparse(self.list_url).netloc

        for item in anchors:
            url = item.get("href", "")
            title = item.get("text", "")
            if not url or host not in url or url in seen:
                continue
            if self.link_pattern not in url:
                continue
            if len(title) < 12:
                continue

            seen.add(url)
            articles.append(
                RawArticle(
                    source=self.source,
                    url=url.split("#")[0],
                    title=title,
                    body=title,
                    published_at=None,
                )
            )
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break

        return articles


class ReutersNewsScraper(PlaywrightNewsScraper):
    source = "reuters"
    list_url = "https://www.reuters.com/markets/commodities/"
    link_pattern = "reuters.com"

    async def fetch(self) -> list[RawArticle]:
        from playwright.async_api import async_playwright

        articles: list[RawArticle] = []
        seen: set[str] = set()

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random_user_agent())
            page = await context.new_page()
            try:
                await page.goto(
                    self.list_url,
                    wait_until="domcontentloaded",
                    timeout=45_000,
                )
                await page.wait_for_timeout(3_000)
                anchors = await page.eval_on_selector_all(
                    "a[data-testid='Heading'], a[data-testid='Link'], a[href*='/markets/']",
                    """elements => elements.map(el => ({
                        href: el.href,
                        text: (el.innerText || el.textContent || '').trim()
                    }))""",
                )
            finally:
                await context.close()
                await browser.close()

        for item in anchors:
            url = item.get("href", "")
            title = item.get("text", "")
            if not url or "reuters.com" not in url or url in seen:
                continue
            if "/markets/" not in url and "/world/" not in url and "/business/" not in url:
                continue
            if len(title) < 12:
                continue

            seen.add(url)
            articles.append(
                RawArticle(
                    source=self.source,
                    url=url.split("#")[0],
                    title=title,
                    body=title,
                    published_at=None,
                )
            )
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break

        return articles


class BloombergNewsScraper(PlaywrightNewsScraper):
    source = "bloomberg"
    list_url = "https://www.bloomberg.com/markets/commodities"
    link_pattern = "bloomberg.com"


NEWS_SCRAPERS: dict[str, NewsScraper] = {
    "kitco": KitcoNewsScraper(),
    "fed": FedNewsScraper(),
    "cnbc": CnbcNewsScraper(),
    "reuters": ReutersNewsScraper(),
    "bloomberg": BloombergNewsScraper(),
}


def get_news_scrapers(source: str | None = None) -> list[NewsScraper]:
    if source:
        key = source.lower()
        if key not in NEWS_SCRAPERS:
            raise ValueError(
                f"Unknown source '{source}'. "
                f"Available: {', '.join(sorted(NEWS_SCRAPERS))}"
            )
        return [NEWS_SCRAPERS[key]]
    return list(NEWS_SCRAPERS.values())


async def run_news_scraper(scraper: NewsScraper) -> ScrapeRunRecord:
    started = time.perf_counter()
    try:
        articles = await scraper.fetch()
        duration_ms = int((time.perf_counter() - started) * 1000)
        status = ScrapeStatus.SUCCESS if articles else ScrapeStatus.PARTIAL
        return ScrapeRunRecord(
            source=scraper.source,
            status=status,
            duration_ms=duration_ms,
            article_count=len(articles),
            error=None if articles else "No articles extracted",
        ), articles
    except Exception as exc:  # noqa: BLE001 - per-source isolation
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ScrapeRunRecord(
            source=scraper.source,
            status=ScrapeStatus.FAILED,
            duration_ms=duration_ms,
            article_count=0,
            error=str(exc),
        ), []
