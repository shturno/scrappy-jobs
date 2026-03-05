"""Programathor scraper — extracts job listings via httpx + BeautifulSoup."""

import asyncio
import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

_BASE_URL = "https://programathor.com.br"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PAGES = (1, 2, 3)
_URLS = [
    f"{_BASE_URL}/jobs-react",
    f"{_BASE_URL}/jobs-frontend",
    f"{_BASE_URL}/jobs-typescript",
    f"{_BASE_URL}/jobs-fullstack",
]


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _is_expired_card(card_div: Tag) -> bool:
    return "Vencida" in card_div.get_text(" ", strip=True)


def _parse_company(content: Tag) -> str:
    icon_div = content.select_one(".cell-list-content-icon")
    if not icon_div:
        return ""
    first_span = icon_div.find("span")
    if not isinstance(first_span, Tag):
        return ""
    for icon in first_span.find_all("i"):
        icon.decompose()
    return first_span.get_text(strip=True)


def _parse_card(card_div: Tag) -> Optional[dict]:
    link = card_div.find("a", href=True)
    if not isinstance(link, Tag):
        return None
    if _is_expired_card(card_div):
        return None

    href = str(link.get("href", ""))
    url = href if href.startswith("http") else f"{_BASE_URL}{href}"

    content = card_div.select_one(".cell-list-content")
    if not content:
        return None

    h3 = content.find("h3")
    if not h3 or not isinstance(h3, Tag):
        return None
    for badge in h3.find_all("span"):
        badge.decompose()
    title = h3.get_text(strip=True)
    if not title or not url:
        return None

    return {
        "title": title,
        "company": _parse_company(content),
        "url": url,
        "description": "",
        "email": None,
    }


def _parse_cards(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for card_div in soup.select("div.cell-list"):
        job = _parse_card(card_div)
        if job:
            results.append(job)
    return results


async def _fetch_page(
    client: httpx.AsyncClient, base_url: str, page: int
) -> list[dict]:
    url = base_url if page == 1 else f"{base_url}?page={page}"
    try:
        await asyncio.sleep(1.5)
        r = await client.get(url)
        if r.status_code == 429:
            logger.warning("Programathor 429 for %s page %d — skipping", base_url, page)
            await asyncio.sleep(3)
            return []
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return _parse_cards(r.text)
    except Exception as exc:
        logger.warning("Programathor error [%s/p%d]: %s", base_url, page, exc)
        return []


async def fetch_programathor_jobs(
    _keywords: list[str],
    _cities: list[str],
) -> list[dict]:
    """Scrape Programathor job listings across 4 category pages, 3 pages each.

    The `_keywords` and `_cities` params are accepted for API consistency
    but Programathor uses fixed category URLs for frontend/fullstack roles.
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=20, follow_redirects=True) as client:
        tasks = [
            _fetch_page(client, base_url, page)
            for base_url in _URLS
            for page in _PAGES
        ]
        results = await asyncio.gather(*tasks)

    jobs: list[dict] = []
    for batch in results:
        jobs.extend(batch)
    logger.info("Programathor: %d jobs found", len(jobs))
    return jobs
