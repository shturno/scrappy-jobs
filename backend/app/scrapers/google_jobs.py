"""Google Custom Search API scraper — fetches jobs by keyword + city.

IMPORTANT: Google CSE has 100 free queries/day limit.
This scraper:
- Makes sequential requests (not parallel) to control request volume
- Logs request count daily in GOOGLE_CSE_DAILY_LOG env var file
- Skips scraping if daily limit (GOOGLE_CSE_DAILY_LIMIT) would be exceeded
"""

import asyncio
import json
import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_GOOGLE_URL = "https://customsearch.googleapis.com/customsearch/v1"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_DAILY_LIMIT = int(os.getenv("GOOGLE_CSE_DAILY_LIMIT", "80"))  # Leave 20 buffer
_LOG_FILE = Path(os.getenv("GOOGLE_CSE_DAILY_LOG", "/tmp/google_cse_daily.json"))


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _get_daily_count() -> int:
    """Read today's request count from log file."""
    if not _LOG_FILE.exists():
        return 0
    try:
        data = json.loads(_LOG_FILE.read_text())
        today = datetime.now(UTC).date().isoformat()
        if data.get("date") == today:
            return data.get("count", 0)
    except (json.JSONDecodeError, OSError):
        pass
    return 0


def _increment_daily_count() -> int:
    """Increment and save today's request count. Returns new count."""
    today = datetime.now(UTC).date().isoformat()
    current = _get_daily_count()
    new_count = current + 1
    try:
        _LOG_FILE.write_text(json.dumps({"date": today, "count": new_count}))
    except OSError:
        logger.warning("Failed to write Google CSE daily log")
    return new_count


def _can_make_request() -> bool:
    """Check if we can make another request today."""
    return _get_daily_count() < _DAILY_LIMIT


def _normalize_result(item: dict) -> Optional[dict]:
    url = item.get("link")
    if not url:
        return None
    title = item.get("title", "")
    snippet = item.get("snippet", "")
    pagemap = item.get("pagemap", {})
    metatags = pagemap.get("metatags", [{}])[0] if pagemap.get("metatags") else {}
    company = metatags.get("og:site_name", "") or urlparse(url).netloc
    return {
        "title": title,
        "company": company,
        "url": url,
        "description": snippet,
        "email": _extract_email(snippet),
    }


async def _search_pair(
    client: httpx.AsyncClient,
    api_key: str,
    cse_id: str,
    keyword: str,
    city: str,
) -> list[dict]:
    """Make a single search. Increments daily request counter."""
    if not _can_make_request():
        logger.warning(
            "Google CSE daily limit (%d) reached — skipping '%s/%s'",
            _DAILY_LIMIT,
            keyword,
            city,
        )
        return []

    query = f"{keyword} vaga {city}"
    params = {"key": api_key, "cx": cse_id, "q": query, "num": 10}
    try:
        await asyncio.sleep(1.5)  # 1.5s between requests for safety
        r = await client.get(_GOOGLE_URL, params=params)
        _increment_daily_count()  # Count both success and error requests

        if r.status_code == 429:
            logger.warning("Google CSE 429 for '%s' — skipping", query)
            return []
        r.raise_for_status()
        items = r.json().get("items", [])
        results = []
        for item in items:
            job = _normalize_result(item)
            if job:
                results.append(job)
        logger.debug("Google CSE '%s': %d jobs", query, len(results))
        return results
    except Exception as exc:
        logger.warning("Google CSE error [%s/%s]: %s", keyword, city, exc)
        return []


async def fetch_google_jobs(keywords: list[str], cities: list[str]) -> list[dict]:
    """Search Google Custom Search API for every keyword × city pair.

    Makes SEQUENTIAL requests (not parallel) to avoid burning through daily limit.
    Returns normalized job dicts (same schema as fetch_gupy_jobs).
    Returns [] immediately if GOOGLE_API_KEY or GOOGLE_CSE_ID are not set.
    Respects GOOGLE_CSE_DAILY_LIMIT (default 80 of 100 free/day).
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    cse_id = os.getenv("GOOGLE_CSE_ID", "")

    if not api_key or not cse_id:
        logger.warning(
            "GOOGLE_API_KEY or GOOGLE_CSE_ID not set — skipping Google Jobs scraper."
        )
        return []

    current = _get_daily_count()
    expected = len(keywords) * len(cities)
    if current + expected > _DAILY_LIMIT:
        logger.warning(
            "Google CSE: %d requests today, would exceed limit of %d if fetching all %d keyword×city pairs",
            current,
            _DAILY_LIMIT,
            expected,
        )

    jobs: list[dict] = []
    async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
        for kw in keywords:
            for city in cities:
                batch = await _search_pair(client, api_key, cse_id, kw, city)
                jobs.extend(batch)

    logger.info("Google Jobs: %d jobs found (daily request count: %d/%d)", len(jobs), _get_daily_count(), _DAILY_LIMIT)
    return jobs
