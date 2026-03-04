"""Jooble API scraper — fetches jobs by keyword + city."""

import asyncio
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_JOOBLE_BASE = "https://jooble.org/api"
_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _normalize(raw: dict) -> Optional[dict]:
    url = raw.get("link")
    if not url:
        return None
    snippet = raw.get("snippet", "")
    return {
        "title": raw.get("title", ""),
        "company": raw.get("company", ""),
        "url": url,
        "description": snippet,
        "email": _extract_email(snippet),
    }


async def _fetch_for_keyword(
    client: httpx.AsyncClient, api_key: str, keyword: str
) -> list[dict]:
    url = f"{_JOOBLE_BASE}/{api_key}"
    payload = {"keywords": keyword, "country": "br", "resultsOnPage": 20}
    try:
        await asyncio.sleep(1.5)
        r = await client.post(url, json=payload)
        if r.status_code == 429:
            logger.warning("Jooble 429 for %s — skipping", keyword)
            return []
        r.raise_for_status()
        jobs_raw = r.json().get("jobs", [])
        results = []
        for raw in jobs_raw:
            job = _normalize(raw)
            if job:
                results.append(job)
        return results
    except Exception as exc:
        logger.warning("Jooble error [%s]: %s", keyword, exc)
        return []


async def fetch_jooble_jobs(keywords: list[str], _cities: list[str]) -> list[dict]:
    """Fetch jobs from Jooble for every keyword, scoped to Brazil (country=br).

    The `cities` parameter is accepted for API consistency but not used —
    Jooble does not support Brazilian city names as location strings.
    Returns [] immediately if JOOBLE_API_KEY is not set.
    """
    api_key = os.getenv("JOOBLE_API_KEY", "")
    if not api_key:
        logger.warning("JOOBLE_API_KEY not set — skipping Jooble scraper.")
        return []

    async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
        tasks = [
            _fetch_for_keyword(client, api_key, kw)
            for kw in keywords
        ]
        results = await asyncio.gather(*tasks)

    jobs: list[dict] = []
    for batch in results:
        jobs.extend(batch)
    return jobs
