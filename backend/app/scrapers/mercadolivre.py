import asyncio
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_ML_API = "https://careers.mercadolibre.com/api/offers"
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


async def fetch_mercadolivre_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=20) as client:
            page = 1
            while page <= 5:
                params = {"country": "BR", "page": page}
                await asyncio.sleep(1.5)

                try:
                    r = await client.get(_ML_API, params=params)
                    if r.status_code != 200:
                        logger.warning("Mercado Livre page %d returned %d", page, r.status_code)
                        break

                    data = r.json()
                    results = data if isinstance(data, list) else data.get("offers", [])

                    if not results:
                        break

                    for job in results:
                        title = job.get("title", "")
                        location = job.get("location", "")
                        url = job.get("url", "")

                        if not url:
                            continue

                        description = job.get("description", "")

                        jobs.append({
                            "title": title,
                            "company": "Mercado Livre",
                            "url": url,
                            "description": description,
                            "email": _extract_email(description),
                        })

                    page += 1

                except Exception as exc:
                    logger.warning("Mercado Livre page %d error: %s", page, exc)
                    break

    except Exception as exc:
        logger.warning("Mercado Livre scraper error: %s", exc)

    logger.info("Mercado Livre: %d jobs found", len(jobs))
    return jobs
