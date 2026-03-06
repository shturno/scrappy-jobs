"""Gupy public API scraper — fetches jobs by keyword + city with pagination."""

import asyncio
import logging
import re
from datetime import UTC, datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_GUPY_URL = "https://portal.api.gupy.io/api/v1/jobs"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_LIMIT = 50
_MAX_PAGES = 3


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _is_expired(deadline: str | None) -> bool:
    """Return True if the deadline string represents a past date."""
    if not deadline:
        return False
    try:
        dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        return dt < datetime.now(UTC)
    except ValueError:
        return False


def _normalize(raw: dict) -> Optional[dict]:
    url = raw.get("jobUrl")
    if not url:
        return None
    if raw.get("isActive") is False:
        return None
    if _is_expired(raw.get("applicationDeadline")):
        return None
    return {
        "title": raw.get("name", ""),
        "company": (raw.get("company") or {}).get("name", ""),
        "url": url,
        "description": raw.get("description") or "",
        "email": _extract_email(raw.get("description")),
    }


async def _fetch_page(
    client: httpx.AsyncClient,
    keyword: str,
    city: Optional[str],
    offset: int,
) -> tuple[list[dict], int]:
    """Fetch a single page. Returns (jobs, total) where total is the API's total count."""
    params: dict = {
        "jobName": keyword,
        "limit": _LIMIT,
        "offset": offset,
        "isActive": "true",
    }
    if city:
        params["city"] = city
    else:
        params["workplaceType"] = "remote"
    try:
        await asyncio.sleep(1.5)
        r = await client.get(_GUPY_URL, params=params)
        if r.status_code == 429:
            logger.warning("Gupy 429 for '%s' offset=%d — skipping", keyword, offset)
            await asyncio.sleep(3)
            return [], 0
        r.raise_for_status()
        body = r.json()
        total = body.get("pagination", {}).get("total", 0)
        results = []
        for raw in body.get("data", []):
            job = _normalize(raw)
            if job:
                results.append(job)
        return results, total
    except Exception as exc:
        logger.warning("Gupy error ['%s' offset=%d]: %s", keyword, offset, exc)
        return [], 0


async def _fetch_all_pages(
    client: httpx.AsyncClient, keyword: str, city: Optional[str]
) -> list[dict]:
    """Fetch up to _MAX_PAGES pages for a keyword+city pair."""
    first_jobs, total = await _fetch_page(client, keyword, city, offset=0)
    jobs = list(first_jobs)

    remaining_pages = min(_MAX_PAGES - 1, (total - _LIMIT) // _LIMIT)
    for page in range(1, remaining_pages + 1):
        page_jobs, _ = await _fetch_page(client, keyword, city, offset=page * _LIMIT)
        jobs.extend(page_jobs)

    return jobs


async def fetch_gupy_jobs(keywords: list[str], cities: list[str]) -> list[dict]:
    """Scrape Gupy for every keyword × city pair with pagination.

    Also sweeps remote jobs (no city) for each keyword to capture BR remote roles.
    Returns normalized job dicts.
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
        tasks = [
            _fetch_all_pages(client, kw, city)
            for kw in keywords
            for city in cities
        ]
        tasks += [_fetch_all_pages(client, kw, None) for kw in keywords]
        results = await asyncio.gather(*tasks)

    jobs: list[dict] = []
    for batch in results:
        jobs.extend(batch)
    logger.info("Gupy: %d jobs fetched", len(jobs))
    return jobs
