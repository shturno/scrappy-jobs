import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_AMAZON_API = "https://www.amazon.jobs/en/search.json"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

_BR_CITIES = [
    "sao paulo", "são paulo", "sp", "curitiba", "belo horizonte",
    "recife", "salvador", "brasilia", "brasília", "rj", "rio de janeiro",
]


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _is_brazil_job(location: str) -> bool:
    location_lower = location.lower()
    return any(city in location_lower for city in _BR_CITIES) or "brazil" in location_lower or "brasil" in location_lower


async def fetch_amazon_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
            for page in range(1, 4):
                params = {
                    "base_query": "",
                    "city": "",
                    "country": "BRA",
                    "country_code": "BRA",
                    "page": page,
                    "radius": "24km",
                }
                await asyncio.sleep(1.5)

                try:
                    r = await client.get(_AMAZON_API, params=params)
                    if r.status_code != 200:
                        logger.warning("Amazon page %d returned %d", page, r.status_code)
                        continue

                    data = r.json()
                    results = data.get("jobs", [])

                    if not results:
                        break

                    for job in results:
                        title = job.get("title", "")
                        location = job.get("location", [])
                        location_str = ", ".join(location) if isinstance(location, list) else str(location)

                        if not _is_brazil_job(location_str):
                            continue

                        url = job.get("job_path", "")
                        if not url:
                            continue

                        if not url.startswith("http"):
                            url = f"https://www.amazon.jobs{url}"

                        description = job.get("description_short", "")

                        jobs.append({
                            "title": title,
                            "company": "Amazon",
                            "url": url,
                            "description": description,
                            "email": _extract_email(description),
                        })

                except Exception as exc:
                    logger.warning("Amazon page %d error: %s", page, exc)
                    continue

    except Exception as exc:
        logger.warning("Amazon scraper error: %s", exc)

    logger.info("Amazon: %d jobs found", len(jobs))
    return jobs
