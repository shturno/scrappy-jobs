"""Indeed BR scraper — RSS-based job search for Brazil.

Uses Indeed's public RSS feeds (?rss=1) to avoid anti-bot 403 blocks
that affect HTML scraping from cloud IPs (Railway, etc.).
"""

import asyncio
import logging
import os
import re
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

_RSS_URL = "https://br.indeed.com/jobs"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_REQUEST_DELAY = 2.0  # seconds between requests


def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def _parse_rss(xml_text: str) -> list[dict]:
    """Parse Indeed RSS feed XML into job dicts."""
    results: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.warning("Indeed BR RSS parse error: %s", exc)
        return results

    channel = root.find("channel")
    if channel is None:
        return results

    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        company_el = item.find("source")
        desc_el = item.find("description")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        url = link_el.text.strip() if link_el is not None and link_el.text else ""
        company = (
            company_el.text.strip()
            if company_el is not None and company_el.text
            else ""
        )
        description = (
            desc_el.text.strip() if desc_el is not None and desc_el.text else ""
        )

        if not title or not url:
            continue

        results.append(
            {
                "title": title,
                "company": company,
                "url": url,
                "description": description,
                "email": _extract_email(description),
            }
        )
    return results


async def _fetch_rss(
    client: httpx.AsyncClient, keyword: str, city: str
) -> list[dict]:
    params = {
        "q": keyword,
        "l": city,
        "rss": "1",
        "limit": "20",
        "sort": "date",
    }
    try:
        await asyncio.sleep(_REQUEST_DELAY)
        r = await client.get(_RSS_URL, params=params)
        if r.status_code == 429:
            logger.warning("Indeed BR RSS 429 for '%s'/'%s' — skipping", keyword, city)
            return []
        if r.status_code != 200:
            logger.warning(
                "Indeed BR RSS %d for '%s'/'%s'", r.status_code, keyword, city
            )
            return []
        jobs = _parse_rss(r.text)
        logger.debug("Indeed BR RSS '%s'/'%s': %d jobs", keyword, city, len(jobs))
        return jobs
    except Exception as exc:
        logger.warning("Indeed BR RSS error ['%s'/'%s']: %s", keyword, city, exc)
        return []


async def fetch_indeed_br_jobs(
    keywords: list[str],
    cities: list[str],
) -> list[dict]:
    """Scrape Indeed BR via RSS for every keyword × city pair.

    Controlled by ENABLE_INDEED_BR env var (default 'true').
    Requests are made sequentially to respect rate limits.
    Returns [] if disabled or on any unrecoverable error.
    """
    if os.getenv("ENABLE_INDEED_BR", "true").lower() == "false":
        logger.info("Indeed BR scraper disabled via ENABLE_INDEED_BR=false")
        return []

    jobs: list[dict] = []
    async with httpx.AsyncClient(
        headers=_HEADERS, timeout=20, follow_redirects=True
    ) as client:
        for kw in keywords:
            for city in cities:
                batch = await _fetch_rss(client, kw, city)
                jobs.extend(batch)

    logger.info("Indeed BR RSS: %d jobs found", len(jobs))
    return jobs
