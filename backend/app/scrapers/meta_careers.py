import asyncio
import json
import logging
import os
import re
from typing import Optional
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

_META_GRAPHQL = "https://www.metacareers.com/graphql"
_SCRAPERAPI_URL = "http://api.scraperapi.com"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _build_url(api_key: str) -> str:
    target_url = _META_GRAPHQL
    proxy_params = urlencode({"api_key": api_key, "url": target_url})
    return f"{_SCRAPERAPI_URL}?{proxy_params}"


async def fetch_meta_careers_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    api_key = os.getenv("SCRAPER_API_KEY", "")
    if not api_key:
        logger.warning("SCRAPER_API_KEY not set — skipping Meta careers scraper")
        return []

    jobs: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
            query = {
                "operationName": "CareersJobSearchPageQuery",
                "variables": {
                    "locations": ["São Paulo"],
                    "limit": 20,
                    "offset": 0,
                },
                "query": "query CareersJobSearchPageQuery { jobs { id title location url description } }"
            }

            await asyncio.sleep(2.0)

            try:
                url = _build_url(api_key)
                r = await client.post(url, json=query)

                if r.status_code != 200:
                    logger.warning("Meta careers returned %d", r.status_code)
                    return jobs

                data = r.json()
                results = data.get("data", {}).get("jobs", [])

                for job in results:
                    title = job.get("title", "")
                    location = job.get("location", "")

                    if "brazil" not in location.lower() and "são paulo" not in location.lower():
                        continue

                    url = job.get("url", "")
                    if not url:
                        continue

                    description = job.get("description", "")

                    jobs.append({
                        "title": title,
                        "company": "Meta",
                        "url": url,
                        "description": description,
                        "email": _extract_email(description),
                    })

            except Exception as exc:
                logger.warning("Meta careers error: %s", exc)

    except Exception as exc:
        logger.warning("Meta careers scraper error: %s", exc)

    logger.info("Meta Careers: %d jobs found", len(jobs))
    return jobs
