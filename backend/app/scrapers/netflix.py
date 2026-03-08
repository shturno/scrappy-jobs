import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_NETFLIX_API = "https://jobs.netflix.com/api/jobs"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _is_brazil_location(location: str) -> bool:
    location_lower = location.lower()
    return any(x in location_lower for x in ["brazil", "brasil", "são paulo"])


async def fetch_netflix_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
            params = {"country": "BR"}
            await asyncio.sleep(1.5)

            try:
                r = await client.get(_NETFLIX_API, params=params)
                if r.status_code != 200:
                    logger.warning("Netflix returned %d", r.status_code)
                    return jobs

                data = r.json()
                results = data if isinstance(data, list) else data.get("jobs", [])

                for job in results:
                    title = job.get("title", "")
                    location = job.get("location", "")

                    if not _is_brazil_location(location):
                        continue

                    url = job.get("jobUrl", "") or job.get("url", "")
                    if not url:
                        continue

                    description = job.get("description", "")

                    jobs.append({
                        "title": title,
                        "company": "Netflix",
                        "url": url,
                        "description": description,
                        "email": _extract_email(description),
                    })

            except Exception as exc:
                logger.warning("Netflix error: %s", exc)

    except Exception as exc:
        logger.warning("Netflix scraper error: %s", exc)

    logger.info("Netflix: %d jobs found", len(jobs))
    return jobs
