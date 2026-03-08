import asyncio, logging, re
from typing import Optional
import httpx
logger = logging.getLogger(__name__)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
def _extract_email(text: Optional[str]) -> Optional[str]:
    if not text: return None
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None
async def fetch_oracle_careers_jobs(_keywords: list[str], _cities: list[str]) -> list[dict]:
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            offset = 0
            while offset < 200:
                await asyncio.sleep(2.0)
                body = {"appliedFacets": {"Country_Region": ["BRA"]}, "limit": 20, "offset": offset}
                r = await client.post("https://oracle.wd1.myworkdayjobs.com/wday/cxs/oracle/oracle/jobs", json=body)
                if r.status_code != 200: break
                data = r.json()
                results = data.get("jobs", [])
                if not results: break
                for job in results:
                    title = job.get("title", "")
                    url = job.get("jobPostingUrl", "")
                    if not url: continue
                    description = job.get("description", "")
                    jobs.append({"title": title, "company": "Oracle", "url": url, "description": description, "email": _extract_email(description)})
                offset += 20
    except Exception as exc:
        logger.warning("Oracle error: %s", exc)
    logger.info("Oracle Careers: %d jobs found", len(jobs))
    return jobs
