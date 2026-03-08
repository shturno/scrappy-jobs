import asyncio, logging, re
from typing import Optional
import httpx
logger = logging.getLogger(__name__)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text: return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None
async def fetch_santander_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            await asyncio.sleep(1.5)
            r = await client.get("https://santander.com.br/api/jobs", params={"country": "BR"})
            if r.status_code != 200: return jobs
            data = r.json()
            results = data if isinstance(data, list) else data.get("jobs", [])
            for job in results:
                title = job.get("title", "")
                url = job.get("url", "")
                if not url: continue
                description = job.get("description", "")
                jobs.append({"title": title, "company": "Santander", "url": url, "description": description, "email": _extract_email(description)})
    except Exception as exc:
        logger.warning("Santander error: %s", exc)
    logger.info("Santander: %d jobs found", len(jobs))
    return jobs
