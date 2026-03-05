"""Arbeitnow API scraper — fetches remote/Brazil jobs by keyword across pages."""

import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_ARBEITNOW_URL = "https://www.arbeitnow.com/api/job-board-api"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PAGES = (1, 2, 3)
_ARBEITNOW_KEYWORDS = ["react", "frontend", "fullstack", "typescript"]
_BRAZIL_TERMS = {"brazil", "brasil", "remote"}


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _is_relevant(job: dict) -> bool:
    if job.get("remote") is True:
        return True
    location = (job.get("location") or "").lower()
    return any(term in location for term in _BRAZIL_TERMS)


def _normalize(raw: dict) -> Optional[dict]:
    url = raw.get("url")
    if not url:
        return None
    description = raw.get("description", "")
    return {
        "title": raw.get("title", ""),
        "company": raw.get("company_name", ""),
        "url": url,
        "description": description,
        "email": _extract_email(description),
    }


async def _fetch_page(
    client: httpx.AsyncClient, keyword: str, page: int
) -> list[dict]:
    params = {"search": keyword, "page": page}
    try:
        await asyncio.sleep(1.0)
        r = await client.get(_ARBEITNOW_URL, params=params)
        if r.status_code == 429:
            logger.warning("Arbeitnow 429 for '%s' page %d — skipping", keyword, page)
            return []
        r.raise_for_status()
        results = []
        for raw in r.json().get("data", []):
            if not _is_relevant(raw):
                continue
            job = _normalize(raw)
            if job:
                results.append(job)
        return results
    except Exception as exc:
        logger.warning("Arbeitnow error [%s/p%d]: %s", keyword, page, exc)
        return []


async def fetch_arbeitnow_jobs(
    _keywords: list[str],
    _cities: list[str],
) -> list[dict]:
    """Fetch remote/Brazil jobs from Arbeitnow across pages 1-3.

    The `_keywords` and `_cities` params are accepted for API consistency
    but Arbeitnow uses its own fixed keyword list tuned for frontend roles.
    Filters results to jobs that are remote or located in Brazil.
    """
    async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
        tasks = [
            _fetch_page(client, kw, page)
            for kw in _ARBEITNOW_KEYWORDS
            for page in _PAGES
        ]
        results = await asyncio.gather(*tasks)

    jobs: list[dict] = []
    for batch in results:
        jobs.extend(batch)
    logger.info("Arbeitnow: %d relevant jobs found", len(jobs))
    return jobs
