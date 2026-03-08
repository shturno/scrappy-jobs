import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_GOOGLE_API = "https://careers.google.com/api/jobs/jobs-v1/search/"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _is_brazil_location(location: str) -> bool:
    location_lower = location.lower()
    return "brazil" in location_lower or "brasil" in location_lower or "são paulo" in location_lower


async def fetch_google_careers_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
            start = 0
            while True:
                params = {
                    "company": "Google",
                    "location": "Brazil",
                    "start": start,
                }
                await asyncio.sleep(1.5)

                try:
                    r = await client.get(_GOOGLE_API, params=params)
                    if r.status_code != 200:
                        logger.warning("Google careers returned %d", r.status_code)
                        break

                    data = r.json()
                    results = data.get("jobs", [])

                    if not results:
                        break

                    for job in results:
                        title = job.get("title", "")
                        location = job.get("location", "")

                        if not _is_brazil_location(location):
                            continue

                        url = job.get("url", "")
                        if not url:
                            continue

                        description = job.get("description", "")

                        jobs.append({
                            "title": title,
                            "company": "Google",
                            "url": url,
                            "description": description,
                            "email": _extract_email(description),
                        })

                    start += len(results)
                    if len(results) < 10:
                        break

                except Exception as exc:
                    logger.warning("Google careers error at start=%d: %s", start, exc)
                    break

    except Exception as exc:
        logger.warning("Google careers scraper error: %s", exc)

    logger.info("Google Careers: %d jobs found", len(jobs))
    return jobs
