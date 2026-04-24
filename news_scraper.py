"""
NSE News Scraper
Scrapes three sources every 30 min and matches headlines to NSE tickers.

Sources:
  - nse.co.ke/listed-company-announcements/  (Playwright — JS-rendered)
  - businessdailyafrica.com/bd/markets        (requests + BS4)
  - kenyanwallstreet.com/category/equities/   (requests + BS4)

Public API:
  scrape_nse_news()          -> list[dict]   (async, call from job)
  get_news_for_tickers(list) -> list[dict]   (sync cache read, call from alerts)
  get_latest_news(n)         -> list[dict]   (sync, for /news command)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR      = os.path.join(os.path.dirname(__file__), "data")
CACHE_FILE    = os.path.join(DATA_DIR, "news_cache.json")
SEEN_FILE     = os.path.join(DATA_DIR, "seen_urls.json")
MAX_CACHE     = 200          # max items kept in memory / cache file
SCRAPE_TTL    = 1800         # 30 min — skip if last scrape was fresher
OUTSIDE_TTL   = 7200         # 2 h  — skip outside market hours if fresher

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# All 56 NSE Kenya tickers — used for text matching
NSE_TICKERS: frozenset[str] = frozenset({
    "ABSA", "ARM", "BAMB", "BAT", "BBCD", "BOC", "BRIT", "CABL", "CARB",
    "CFC", "CIC", "COOP", "CURB", "DBLE", "DTK", "DTKE", "EABL", "EGAD",
    "EQTY", "EVRD", "FAHR", "FIRE", "GBK", "GRIT", "HAFR", "HF", "I&M",
    "JUB", "KALI", "KAPC", "KCB", "KCSE", "KEGN", "KQ", "KPLC", "KNRE",
    "KPC", "KPL", "LKL", "LIMT", "MCOM", "MSBO", "NABO", "NBK", "NCBA",
    "NSE", "NTWK", "OCH", "PAFR", "PAKA", "SASN", "SBIC", "SCBK", "SCOM",
    "SLAM", "TOTL", "TPSE", "UCHM", "UNGA", "UMME", "WTK",
})

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

_news_cache: list[dict] = []       # [{headline, url, tickers, source, ts}]
_seen_urls:  set[str]   = set()
_last_scrape: float     = 0.0


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _load_cache() -> None:
    global _news_cache, _seen_urls
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, encoding="utf-8") as f:
                _news_cache = json.load(f)
    except Exception:
        _news_cache = []
    try:
        if os.path.exists(SEEN_FILE):
            with open(SEEN_FILE, encoding="utf-8") as f:
                _seen_urls = set(json.load(f))
    except Exception:
        _seen_urls = set()


def _save_cache() -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_news_cache[-MAX_CACHE:], f)
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(list(_seen_urls)[-2000:], f)
    except Exception as exc:
        logger.warning("news_scraper: cache save failed — %s", exc)


# ---------------------------------------------------------------------------
# Ticker extraction
# ---------------------------------------------------------------------------

def _extract_tickers(text: str) -> list[str]:
    """Return NSE tickers mentioned in text (case-insensitive word match)."""
    words = set(re.findall(r"\b[A-Z]{2,7}\b", text.upper()))
    return sorted(words & NSE_TICKERS)


# ---------------------------------------------------------------------------
# Source 1: Business Daily Africa (requests + BS4)
# ---------------------------------------------------------------------------

def _scrape_bda() -> list[dict]:
    items: list[dict] = []
    try:
        r = requests.get(
            "https://www.businessdailyafrica.com/bd/markets",
            headers=HEADERS, timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("h3 a, h2 a, .article-title a")[:30]:
            headline = a.get_text(strip=True)
            href = a.get("href", "")
            if not headline or len(headline) < 15:
                continue
            url = href if href.startswith("http") else f"https://www.businessdailyafrica.com{href}"
            if url in _seen_urls:
                continue
            items.append({
                "headline": headline,
                "url": url,
                "tickers": _extract_tickers(headline),
                "source": "BusinessDailyAfrica",
                "ts": datetime.now(timezone.utc).isoformat(),
            })
    except Exception as exc:
        logger.warning("BDA scrape failed: %s", exc)
    return items


# ---------------------------------------------------------------------------
# Source 2: Kenyan Wall Street (requests + BS4)
# ---------------------------------------------------------------------------

def _scrape_kws() -> list[dict]:
    items: list[dict] = []
    try:
        r = requests.get(
            "https://kenyanwallstreet.com/category/equities/",
            headers=HEADERS, timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("h2.entry-title a, h3.entry-title a, .post-title a")[:30]:
            headline = a.get_text(strip=True)
            url = a.get("href", "")
            if not headline or len(headline) < 15 or not url:
                continue
            if url in _seen_urls:
                continue
            items.append({
                "headline": headline,
                "url": url,
                "tickers": _extract_tickers(headline),
                "source": "KenyanWallStreet",
                "ts": datetime.now(timezone.utc).isoformat(),
            })
    except Exception as exc:
        logger.warning("KWS scrape failed: %s", exc)
    return items


# ---------------------------------------------------------------------------
# Source 3: NSE Announcements (Playwright — JS-rendered)
# ---------------------------------------------------------------------------

async def _scrape_nse_announcements() -> list[dict]:
    items: list[dict] = []
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            page = await browser.new_page()
            await page.set_extra_http_headers({"User-Agent": HEADERS["User-Agent"]})
            await page.goto(
                "https://www.nse.co.ke/listed-company-announcements/",
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            await page.wait_for_timeout(3000)  # let JS render

            rows = await page.query_selector_all("table tr, .announcement-row, .item-row")
            for row in rows[:40]:
                text = (await row.inner_text()).strip()
                if not text or len(text) < 20:
                    continue
                # Try to extract a link
                link_el = await row.query_selector("a")
                url = ""
                if link_el:
                    url = await link_el.get_attribute("href") or ""
                    if url and not url.startswith("http"):
                        url = f"https://www.nse.co.ke{url}"

                first_line = text.split("\n")[0].strip()
                if not first_line or url in _seen_urls:
                    continue
                items.append({
                    "headline": first_line,
                    "url": url or "https://www.nse.co.ke/listed-company-announcements/",
                    "tickers": _extract_tickers(text),
                    "source": "NSE",
                    "ts": datetime.now(timezone.utc).isoformat(),
                })
            await browser.close()
    except ImportError:
        logger.debug("Playwright not installed — NSE announcement scrape skipped")
    except Exception as exc:
        logger.warning("NSE announcement scrape failed: %s", exc)
    return items


# ---------------------------------------------------------------------------
# Main scrape orchestrator
# ---------------------------------------------------------------------------

async def scrape_nse_news(force: bool = False) -> list[dict]:
    """
    Scrape all three sources. Returns list of NEW items added this run.
    Skips if cache is fresh enough (respects SCRAPE_TTL / OUTSIDE_TTL).
    """
    global _news_cache, _seen_urls, _last_scrape

    if not _news_cache and not _seen_urls:
        _load_cache()

    now = time.time()
    if not force and (now - _last_scrape) < SCRAPE_TTL:
        logger.debug("news_scraper: cache fresh (%.0fs ago), skipping", now - _last_scrape)
        return []

    logger.info("news_scraper: scraping all sources")

    # Run BS4 sources in thread pool, Playwright concurrently
    loop = asyncio.get_event_loop()
    bda_fut = loop.run_in_executor(None, _scrape_bda)
    kws_fut = loop.run_in_executor(None, _scrape_kws)
    nse_fut = _scrape_nse_announcements()

    bda_items, kws_items, nse_items = await asyncio.gather(bda_fut, kws_fut, nse_fut)

    new_items: list[dict] = []
    for item in (bda_items + kws_items + nse_items):
        if item["url"] and item["url"] in _seen_urls:
            continue
        new_items.append(item)
        _seen_urls.add(item["url"])

    if new_items:
        _news_cache = (new_items + _news_cache)[:MAX_CACHE]
        _save_cache()
        logger.info("news_scraper: %d new items (%d BDA, %d KWS, %d NSE)",
                    len(new_items), len(bda_items), len(kws_items), len(nse_items))

    _last_scrape = now
    return new_items


# ---------------------------------------------------------------------------
# Public sync API (for alert jobs and /news command)
# ---------------------------------------------------------------------------

def get_news_for_tickers(tickers: list[str]) -> list[dict]:
    """Return cached news items that mention any of the given tickers."""
    if not _news_cache:
        _load_cache()
    upper = {t.upper() for t in tickers}
    return [item for item in _news_cache if set(item.get("tickers", [])) & upper]


def get_latest_news(n: int = 10) -> list[dict]:
    """Return the n most recent cached news items."""
    if not _news_cache:
        _load_cache()
    return _news_cache[:n]
