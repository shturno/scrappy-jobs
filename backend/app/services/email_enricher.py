"""Email enrichment — finds recruiter email from multiple sources in cascade."""

import asyncio
import logging
import os
import re
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

_PLATFORM_DOMAINS = {
    "gupy.io", "linkedin.com", "indeed.com", "glassdoor.com",
    "infojobs.com.br", "catho.com.br", "vagas.com.br", "trampos.co",
    "programathor.com.br", "arbeitnow.com", "adzuna.com", "jooble.org",
    "google.com",
}

_COMMON_PATTERNS = [
    "rh@{domain}",
    "recrutamento@{domain}",
    "careers@{domain}",
    "hr@{domain}",
    "talentos@{domain}",
    "contato@{domain}",
    "jobs@{domain}",
]


def _extract_domain(url: str) -> Optional[str]:
    """Extract company domain from a URL, returning None for known job platforms."""
    try:
        host = urlparse(url).hostname or ""
        if not host:
            return None
        if any(p in host for p in _PLATFORM_DOMAINS):
            return None
        return host
    except Exception:
        return None


def _first_email(html: str) -> Optional[str]:
    match = _EMAIL_RE.search(html)
    return match.group(0) if match else None


async def _fetch_job_page_email(client: httpx.AsyncClient, job_url: str) -> Optional[str]:
    """Fetch the job page and look for an email in the HTML."""
    try:
        await asyncio.sleep(1.5)
        r = await client.get(job_url, timeout=10)
        if r.status_code == 200:
            return _first_email(r.text)
    except Exception as exc:
        logger.debug("Job page fetch failed for %s: %s", job_url, exc)
    return None


async def _hunter_search(domain: str) -> Optional[str]:
    """Search Hunter.io for a domain email. Requires HUNTER_API_KEY."""
    api_key = os.getenv("HUNTER_API_KEY", "")
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(headers=_HEADERS, timeout=10) as client:
            r = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": api_key, "limit": 1},
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                emails = data.get("emails", [])
                if emails:
                    return emails[0].get("value")
    except Exception as exc:
        logger.debug("Hunter.io failed for %s: %s", domain, exc)
    return None


async def _snov_search(domain: str) -> Optional[str]:
    """Search Snov.io for a domain email. Requires SNOV_CLIENT_ID and SNOV_CLIENT_SECRET."""
    client_id = os.getenv("SNOV_CLIENT_ID", "")
    client_secret = os.getenv("SNOV_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token_r = await client.post(
                "https://api.snov.io/v1/oauth/access_token",
                data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
            )
            token = token_r.json().get("access_token", "")
            if not token:
                return None
            search_r = await client.get(
                "https://api.snov.io/v1/get-domain-emails-with-info",
                params={"domain": domain, "type": "all", "limit": 1},
                headers={"Authorization": f"Bearer {token}"},
            )
            if search_r.status_code == 200:
                emails = search_r.json().get("emails", [])
                if emails:
                    return emails[0].get("email")
    except Exception as exc:
        logger.debug("Snov.io failed for %s: %s", domain, exc)
    return None


def _infer_email(domain: str) -> Optional[str]:
    """Return first pattern-guessed email (unverified)."""
    return _COMMON_PATTERNS[0].format(domain=domain)


async def enrich_email(job_url: str) -> Optional[str]:
    """Try 4 sources in cascade to find a recruiter email for the job.

    1. Fetch job page HTML and regex for email
    2. Hunter.io domain search (if HUNTER_API_KEY set)
    3. Snov.io domain search (if SNOV_CLIENT_ID + SNOV_CLIENT_SECRET set)
    4. Infer common pattern (rh@domain)

    Returns the first email found, or None if all sources fail.
    """
    async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True) as client:
        email = await _fetch_job_page_email(client, job_url)
        if email:
            logger.debug("Email found via job page: %s", email)
            return email

    domain = _extract_domain(job_url)
    if not domain:
        return None

    email = await _hunter_search(domain)
    if email:
        logger.debug("Email found via Hunter.io: %s", email)
        return email

    email = await _snov_search(domain)
    if email:
        logger.debug("Email found via Snov.io: %s", email)
        return email

    email = _infer_email(domain)
    if email:
        logger.debug("Email inferred via pattern: %s", email)
    return email
