"""Indeed BR scraper — HTML-based job search for Brazil."""

import asyncio
import logging
import os
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

_INDEED_URL = "https://br.indeed.com/empregos"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml",
}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_JOB_URL_BASE = "https://br.indeed.com"


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _parse_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for card in soup.select("div[data-jk]"):
        title_el = card.select_one("h2 a[data-jk]")
        if not isinstance(title_el, Tag):
            continue
        title = title_el.get_text(strip=True)
        href = str(title_el.get("href", ""))
        url = href if href.startswith("http") else f"{_JOB_URL_BASE}{href}"

        company_el = card.select_one("[data-testid='company-name']")
        company = company_el.get_text(strip=True) if company_el else ""

        snippet_el = card.select_one("[data-testid='job-snippet']")
        description = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        if not title or not url:
            continue

        results.append({
            "title": title,
            "company": company,
            "url": url,
            "description": description,
            "email": _extract_email(description),
        })
    return results


async def _fetch_for_keyword(
    client: httpx.AsyncClient, keyword: str, city: str
) -> list[dict]:
    params = {"q": keyword, "l": city, "limit": 15}
    try:
        await asyncio.sleep(2.0)
        r = await client.get(_INDEED_URL, params=params)
        if r.status_code == 429:
            logger.warning("Indeed BR 429 for '%s'/'%s' — skipping", keyword, city)
            return []
        if r.status_code != 200:
            logger.warning("Indeed BR %d for '%s'/'%s'", r.status_code, keyword, city)
            return []
        return _parse_cards(r.text)
    except Exception as exc:
        logger.warning("Indeed BR error ['%s'/'%s']: %s", keyword, city, exc)
        return []


async def fetch_indeed_br_jobs(
    keywords: list[str],
    cities: list[str],
) -> list[dict]:
    """Scrape Indeed BR via HTML for every keyword × city pair.

    Controlled by ENABLE_INDEED_BR env var (default 'true').
    Returns [] if disabled or on any unrecoverable error.
    """
    if os.getenv("ENABLE_INDEED_BR", "true").lower() == "false":
        logger.info("Indeed BR scraper disabled via ENABLE_INDEED_BR=false")
        return []

    async with httpx.AsyncClient(headers=_HEADERS, timeout=20, follow_redirects=True) as client:
        tasks = [
            _fetch_for_keyword(client, kw, city)
            for kw in keywords
            for city in cities
        ]
        results = await asyncio.gather(*tasks)

    jobs: list[dict] = []
    for batch in results:
        jobs.extend(batch)
    logger.info("Indeed BR: %d jobs found", len(jobs))
    return jobs
