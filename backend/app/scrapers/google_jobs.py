"""Google Custom Search API scraper — fetches jobs by keyword + city."""

import asyncio
import logging
import os
import re
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_GOOGLE_URL = "https://customsearch.googleapis.com/customsearch/v1"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


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
    query = f"{keyword} vaga {city}"
    params = {"key": api_key, "cx": cse_id, "q": query, "num": 10}
    try:
        await asyncio.sleep(1.0)
        r = await client.get(_GOOGLE_URL, params=params)
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
        return results
    except Exception as exc:
        logger.warning("Google CSE error [%s/%s]: %s", keyword, city, exc)
        return []


async def fetch_google_jobs(keywords: list[str], cities: list[str]) -> list[dict]:
    """Search Google Custom Search API for every keyword × city pair.

    Returns normalized job dicts (same schema as fetch_gupy_jobs).
    Returns [] immediately if GOOGLE_API_KEY or GOOGLE_CSE_ID are not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")
    cse_id = os.getenv("GOOGLE_CSE_ID", "")

    if not api_key or not cse_id:
        logger.warning(
            "GOOGLE_API_KEY or GOOGLE_CSE_ID not set — skipping Google Jobs scraper."
        )
        return []

    async with httpx.AsyncClient(headers=_HEADERS, timeout=15) as client:
        tasks = [
            _search_pair(client, api_key, cse_id, kw, city)
            for kw in keywords
            for city in cities
        ]
        results = await asyncio.gather(*tasks)

    jobs: list[dict] = []
    for batch in results:
        jobs.extend(batch)
    return jobs
