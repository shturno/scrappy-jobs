"""Pipeline API — run/scrape/send endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.orchestrator import (
    run_daily_pipeline,
    scrape_only_pipeline,
    send_selected_jobs,
)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineSummary(BaseModel):
    scraped: int
    emails_found: int
    sent: int
    errors: int


class ScrapeResult(BaseModel):
    id: int
    title: str
    company: str
    url: str
    email: str | None
    language: str | None
    status: str


class SendRequest(BaseModel):
    job_ids: list[int]


class SendSummary(BaseModel):
    sent: int
    skipped: int
    errors: int


@router.post("/run", response_model=PipelineSummary)
async def run_pipeline() -> PipelineSummary:
    """Scrape + send in one shot (existing behaviour — do not remove)."""
    result = await run_daily_pipeline()
    return PipelineSummary(
        scraped=result.get("scraped", 0),
        emails_found=result.get("emails_found", 0),
        sent=result.get("sent", 0),
        errors=result.get("errors", 0),
    )


@router.post("/scrape", response_model=list[ScrapeResult])
async def scrape_only() -> list[ScrapeResult]:
    """Scrape jobs and save to DB. Returns list of new jobs. Does NOT send emails."""
    jobs = await scrape_only_pipeline()
    return [
        ScrapeResult(
            id=j.id,  # type: ignore[arg-type]
            title=j.title,
            company=j.company,
            url=j.url,
            email=j.email,
            language=j.language,
            status=j.status,
        )
        for j in jobs
    ]


@router.post("/send", response_model=SendSummary)
def send_selected(body: SendRequest) -> SendSummary:
    """Send emails only for the specified job IDs."""
    result = send_selected_jobs(body.job_ids)
    return SendSummary(
        sent=result.get("sent", 0),
        skipped=result.get("skipped", 0),
        errors=result.get("errors", 0),
    )
