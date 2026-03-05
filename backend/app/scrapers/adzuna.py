"""Adzuna API scraper — fetches BR jobs by keyword across multiple pages."""

import asyncio
import logging
import os
import re
from typing import Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/br/search"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PAGES = (1, 2, 3)
_ADZUNA_KEYWORDS = [
    "desenvolvedor react",
    "frontend developer",
    "react typescript",
    "fullstack",
    "next.js",
]


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _normalize(raw: dict) -> Optional[dict]:
    url = raw.get("redirect_url")
    if not url:
        return None
    description = raw.get("description", "")
    return {
        "title": raw.get("title", ""),
        "company": (raw.get("company") or {}).get("display_name", ""),
        "url": url,
        "description": description,
        "email": _extract_email(description),
    }


async def _fetch_page(
    client: httpx.AsyncClient,
    app_id: str,
    app_key: str,
    keyword: str,
    page: int,
) -> list[dict]:
    url = f"{_ADZUNA_BASE}/{page}"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": keyword,
        "results_per_page": 20,
    }
    try:
        await asyncio.sleep(1.0)
        r = await client.get(url, params=params)
        if r.status_code == 429:
            logger.warning("Adzuna 429 for '%s' page %d — skipping", keyword, page)
            return []
        r.raise_for_status()
        results = []
        for raw in r.json().get("results", []):
            job = _normalize(raw)
            if job:
                results.append(job)
        return results
    except Exception as exc:
        logger.warning("Adzuna error [%s/p%d]: %s", keyword, page, exc)
        return []


async def fetch_adzuna_jobs(
    _keywords: list[str],
    _cities: list[str],
) -> list[dict]:
    """Fetch BR jobs from Adzuna across pages 1-3 for fixed frontend keywords.

    The `_keywords` and `_cities` params are accepted for API consistency
    but Adzuna uses its own fixed keyword list tuned for frontend roles.
    Returns [] immediately if ADZUNA_APP_ID or ADZUNA_APP_KEY are not set.
    """
    app_id = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")

    if not app_id or not app_key:
        logger.warning("ADZUNA_APP_ID or ADZUNA_APP_KEY not set — skipping Adzuna scraper.")
        return []

    async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
        tasks = [
            _fetch_page(client, app_id, app_key, kw, page)
            for kw in _ADZUNA_KEYWORDS
            for page in _PAGES
        ]
        results = await asyncio.gather(*tasks)

    jobs: list[dict] = []
    for batch in results:
        jobs.extend(batch)
    logger.info("Adzuna: %d jobs fetched", len(jobs))
    return jobs
