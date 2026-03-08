import asyncio, logging, re
from typing import Optional
import httpx
logger = logging.getLogger(__name__)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text: return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None
async def fetch_apple_careers_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            await asyncio.sleep(1.5)
            r = await client.get("https://jobs.apple.com/api/role/search", params={"country": "BRA"})
            if r.status_code != 200: return jobs
            data = r.json()
            results = data if isinstance(data, list) else data.get("roles", [])
            for job in results:
                title = job.get("title", "")
                url = job.get("url", "")
                if not url: continue
                description = job.get("description", "")
                jobs.append({"title": title, "company": "Apple", "url": url, "description": description, "email": _extract_email(description)})
    except Exception as exc:
        logger.warning("Apple error: %s", exc)
    logger.info("Apple Careers: %d jobs found", len(jobs))
    return jobs
