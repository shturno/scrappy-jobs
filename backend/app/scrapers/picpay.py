import asyncio, logging, re
from typing import Optional
import httpx
logger = logging.getLogger(__name__)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text: return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None
async def fetch_picpay_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            await asyncio.sleep(1.5)
            r = await client.get("https://api.lever.co/v0/postings/picpay?mode=json")
            if r.status_code != 200: return jobs
            data = r.json()
            for job in data:
                title = job.get("text", "")
                url = job.get("hostedUrl", "")
                if not url: continue
                description = job.get("description", "")
                jobs.append({"title": title, "company": "PicPay", "url": url, "description": description, "email": _extract_email(description)})
    except Exception as exc:
        logger.warning("PicPay error: %s", exc)
    logger.info("PicPay: %d jobs found", len(jobs))
    return jobs
