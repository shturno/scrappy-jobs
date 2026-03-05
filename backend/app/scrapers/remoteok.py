"""RemoteOK public API scraper — fetches remote frontend/fullstack jobs."""

import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_REMOTEOK_URL = "https://remoteok.com/api"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/json",
}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_RELEVANT_TAGS = {
    "react", "frontend", "typescript", "javascript",
    "vue", "nextjs", "fullstack", "next.js", "full-stack",
}


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _is_relevant(job: dict) -> bool:
    tags = {t.lower() for t in (job.get("tags") or [])}
    return bool(tags & _RELEVANT_TAGS)


def _normalize(raw: dict) -> Optional[dict]:
    url = raw.get("url")
    if not url:
        return None
    description = raw.get("description", "")
    return {
        "title": raw.get("position", ""),
        "company": raw.get("company", ""),
        "url": url,
        "description": description,
        "email": _extract_email(description),
    }


async def fetch_remoteok_jobs(
    _keywords: list[str],
    _cities: list[str],
) -> list[dict]:
    """Fetch relevant remote jobs from RemoteOK public API.

    Filters server response to jobs tagged with frontend/JS-related tags.
    The `keywords` and `_cities` params are accepted for API consistency
    but RemoteOK returns a global feed filtered client-side by tags.
    Returns [] on any error.
    """
    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
            r = await client.get(_REMOTEOK_URL)
            r.raise_for_status()
            # First item is always a legal/meta notice dict — skip it
            data = [item for item in r.json() if isinstance(item, dict) and item.get("slug")]
    except Exception as exc:
        logger.warning("RemoteOK error: %s", exc)
        return []

    jobs: list[dict] = []
    for raw in data:
        if not _is_relevant(raw):
            continue
        job = _normalize(raw)
        if job:
            jobs.append(job)

    logger.info("RemoteOK: %d relevant jobs found", len(jobs))
    return jobs
