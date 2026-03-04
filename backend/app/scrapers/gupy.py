"""Gupy public API scraper — fetches jobs by keyword + city."""

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


async def _fetch_for_pair(
    client: httpx.AsyncClient, keyword: str, city: str
) -> list[dict]:
    params = {"jobName": keyword, "city": city, "limit": 20, "isActive": "true"}
    try:
        await asyncio.sleep(1.5)
        r = await client.get(_GUPY_URL, params=params)
        if r.status_code == 429:
            logger.warning("Gupy 429 for %s/%s — skipping", keyword, city)
            await asyncio.sleep(3)
            return []
        r.raise_for_status()
        data = r.json().get("data", [])
        results = []
        for raw in data:
            job = _normalize(raw)
            if job:
                results.append(job)
        return results
    except Exception as exc:
        logger.warning("Gupy error [%s/%s]: %s", keyword, city, exc)
        return []


async def fetch_gupy_jobs(keywords: list[str], cities: list[str]) -> list[dict]:
    """Scrape Gupy for every keyword × city pair. Returns normalized job dicts."""
    async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
        tasks = [
            _fetch_for_pair(client, kw, city)
            for kw in keywords
            for city in cities
        ]
        results = await asyncio.gather(*tasks)

    jobs: list[dict] = []
    for batch in results:
        jobs.extend(batch)
    return jobs
