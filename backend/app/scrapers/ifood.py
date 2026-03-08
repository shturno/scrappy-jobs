import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_IFOOD_API = "https://boards-api.greenhouse.io/v1/boards/ifood/jobs?content=true"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _is_brazil_location(location: str) -> bool:
    location_lower = location.lower()
    return any(x in location_lower for x in ["brazil", "brasil", "são paulo", "remote"])


async def fetch_ifood_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
            await asyncio.sleep(1.5)

            try:
                r = await client.get(_IFOOD_API)
                if r.status_code != 200:
                    logger.warning("iFood returned %d", r.status_code)
                    return jobs

                data = r.json()
                results = data.get("jobs", [])

                for job in results:
                    title = job.get("title", "")
                    location_obj = job.get("location", {})
                    location = location_obj.get("name", "") if isinstance(location_obj, dict) else str(location_obj)

                    if not _is_brazil_location(location):
                        continue

                    url = job.get("absolute_url", "")
                    if not url:
                        continue

                    content = job.get("content", "")

                    jobs.append({
                        "title": title,
                        "company": "iFood",
                        "url": url,
                        "description": content,
                        "email": _extract_email(content),
                    })

            except Exception as exc:
                logger.warning("iFood error: %s", exc)

    except Exception as exc:
        logger.warning("iFood scraper error: %s", exc)

    logger.info("iFood: %d jobs found", len(jobs))
    return jobs
