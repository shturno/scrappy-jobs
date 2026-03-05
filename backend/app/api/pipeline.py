"""Pipeline API — run/scrape/send endpoints."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.dependencies.auth import require_api_key
from app.dependencies.rate_limit import limiter
from app.services.orchestrator import (
    run_daily_pipeline,
    scrape_only_pipeline,
    send_selected_jobs,
)

router = APIRouter(
    prefix="/api/pipeline",
    tags=["pipeline"],
    dependencies=[Depends(require_api_key)],
)


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
@limiter.limit("5/minute")
async def run_pipeline(request: Request) -> PipelineSummary:
    result = await run_daily_pipeline()
    return PipelineSummary(
        scraped=result.get("scraped", 0),
        emails_found=result.get("emails_found", 0),
        sent=result.get("sent", 0),
        errors=result.get("errors", 0),
    )


@router.post("/scrape", response_model=list[ScrapeResult])
@limiter.limit("5/minute")
async def scrape_only(request: Request) -> list[ScrapeResult]:
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
@limiter.limit("5/minute")
def send_selected(request: Request, body: SendRequest) -> SendSummary:
    result = send_selected_jobs(body.job_ids)
    return SendSummary(
        sent=result.get("sent", 0),
        skipped=result.get("skipped", 0),
        errors=result.get("errors", 0),
    )
