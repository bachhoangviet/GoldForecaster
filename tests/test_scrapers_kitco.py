"""Parser tests for Kitco and FED scrapers using fixtures."""

from pathlib import Path

from src.backend.adapters.web_scrapers import FedNewsScraper, KitcoNewsScraper

FIXTURES = Path(__file__).parent / "fixtures"


def test_kitco_parse_fixture():
    html = (FIXTURES / "kitco_news.html").read_text(encoding="utf-8")
    scraper = KitcoNewsScraper()
    articles = scraper.parse(html)

    assert len(articles) == 3
    assert articles[0].source == "kitco"
    assert "gold-prices-rise" in articles[0].url
    assert "Gold prices rise" in articles[0].title


def test_fed_parse_fixture():
    xml_text = (FIXTURES / "fed_feed.xml").read_text(encoding="utf-8")
    scraper = FedNewsScraper()
    articles = scraper.parse(xml_text)

    assert len(articles) == 2
    assert articles[0].source == "fed"
    assert "FOMC statement" in articles[0].title
    assert "federalreserve.gov" in articles[0].url
