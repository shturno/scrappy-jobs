import asyncio
import logging
import os
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.database import engine
from app.models import EmailLog, Job
from app.scrapers.google_jobs import fetch_google_jobs
from app.scrapers.gupy import fetch_gupy_jobs
from app.scrapers.indeed_br import fetch_indeed_br_jobs
from app.scrapers.jooble import fetch_jooble_jobs
from app.scrapers.remoteok import fetch_remoteok_jobs
from app.scrapers.adzuna import fetch_adzuna_jobs
from app.scrapers.arbeitnow import fetch_arbeitnow_jobs
from app.scrapers.programathor import fetch_programathor_jobs
from app.scrapers.amazon import fetch_amazon_jobs
from app.scrapers.google_careers import fetch_google_careers_jobs
from app.scrapers.microsoft_careers import fetch_microsoft_careers_jobs
from app.scrapers.meta_careers import fetch_meta_careers_jobs
from app.scrapers.apple_careers import fetch_apple_careers_jobs
from app.scrapers.netflix import fetch_netflix_jobs
from app.scrapers.spotify import fetch_spotify_jobs
from app.scrapers.uber import fetch_uber_jobs
from app.scrapers.airbnb import fetch_airbnb_jobs
from app.scrapers.salesforce import fetch_salesforce_jobs
from app.scrapers.sap_careers import fetch_sap_careers_jobs
from app.scrapers.oracle_careers import fetch_oracle_careers_jobs
from app.scrapers.ibm_careers import fetch_ibm_careers_jobs
from app.scrapers.samsung_br import fetch_samsung_br_jobs
from app.scrapers.dell_careers import fetch_dell_careers_jobs
from app.scrapers.nubank import fetch_nubank_jobs
from app.scrapers.ifood import fetch_ifood_jobs
from app.scrapers.mercadolivre import fetch_mercadolivre_jobs
from app.scrapers.picpay import fetch_picpay_jobs
from app.scrapers.stone import fetch_stone_jobs
from app.scrapers.rappi import fetch_rappi_jobs
from app.scrapers.inter import fetch_inter_jobs
from app.scrapers.c6bank import fetch_c6bank_jobs
from app.scrapers.itau import fetch_itau_jobs
from app.scrapers.santander import fetch_santander_jobs
from app.services.email_sender import RateLimitExceeded, send_email
from app.services.email_enricher import enrich_email
from app.services.lang_detector import detect_language
from app.services.template_engine import render_template

logger = logging.getLogger(__name__)

_SENDER_VARS = {
    "sender_name": os.getenv("SENDER_NAME", ""),
    "contact_info": os.getenv("SENDER_EMAIL", ""),
    "whatsapp_link": os.getenv("SENDER_WHATSAPP", ""),
    "linkedin_link": os.getenv("SENDER_LINKEDIN", ""),
    "github_link": os.getenv("SENDER_GITHUB", ""),
    "portfolio": os.getenv("SENDER_PORTFOLIO", ""),
}


def _load_config() -> tuple[list[str], list[str]]:
    keywords = [k.strip() for k in os.getenv("SEARCH_KEYWORDS", "developer").split(",")]
    cities = [c.strip() for c in os.getenv("SEARCH_CITIES", "São Paulo").split(",")]
    return keywords, cities


def _load_blocked() -> list[str]:
    raw = os.getenv("BLOCKED_KEYWORDS", "")
    return [k.strip().lower() for k in raw.split(",") if k.strip()]


def _is_blocked(title: str, blocked: list[str]) -> bool:
    """Return True if the job title contains any blocked keyword (case-insensitive)."""
    lower = title.lower()
    return any(kw in lower for kw in blocked)


def _dedup_by_url(jobs: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for job in jobs:
        url = job.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(job)
    return unique


def _url_exists(session: Session, url: str) -> bool:
    return session.exec(select(Job).where(Job.url == url)).first() is not None


def _save_job(session: Session, data: dict, language: str) -> Job:
    job = Job(
        title=data["title"],
        company=data["company"],
        url=data["url"],
        description=data.get("description", ""),
        email=data.get("email"),
        language=language,
        status="new",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _log_email(
    session: Session,
    job: Job,
    subject: str,
    lang: str,
    error: str | None = None,
) -> None:
    log = EmailLog(
        job_id=job.id,  # type: ignore[arg-type]
        subject=subject,
        template_lang=lang,
        sent_at=datetime.now(UTC),
        error_message=error,
    )
    session.add(log)
    session.commit()


async def run_daily_pipeline() -> dict[str, int]:
    keywords, cities = _load_config()
    blocked = _load_blocked()
    summary: dict[str, int] = {"scraped": 0, "emails_found": 0, "sent": 0, "errors": 0}

    results = await asyncio.gather(
        fetch_gupy_jobs(keywords, cities),
        fetch_google_jobs(keywords, cities),
        fetch_jooble_jobs(keywords, cities),
        fetch_remoteok_jobs(keywords, cities),
        fetch_adzuna_jobs(keywords, cities),
        fetch_arbeitnow_jobs(keywords, cities),
        fetch_programathor_jobs(keywords, cities),
        fetch_indeed_br_jobs(keywords, cities),
        fetch_amazon_jobs(keywords, cities),
        fetch_google_careers_jobs(keywords, cities),
        fetch_microsoft_careers_jobs(keywords, cities),
        fetch_meta_careers_jobs(keywords, cities),
        fetch_apple_careers_jobs(keywords, cities),
        fetch_netflix_jobs(keywords, cities),
        fetch_spotify_jobs(keywords, cities),
        fetch_uber_jobs(keywords, cities),
        fetch_airbnb_jobs(keywords, cities),
        fetch_salesforce_jobs(keywords, cities),
        fetch_sap_careers_jobs(keywords, cities),
        fetch_oracle_careers_jobs(keywords, cities),
        fetch_ibm_careers_jobs(keywords, cities),
        fetch_samsung_br_jobs(keywords, cities),
        fetch_dell_careers_jobs(keywords, cities),
        fetch_nubank_jobs(keywords, cities),
        fetch_ifood_jobs(keywords, cities),
        fetch_mercadolivre_jobs(keywords, cities),
        fetch_picpay_jobs(keywords, cities),
        fetch_stone_jobs(keywords, cities),
        fetch_rappi_jobs(keywords, cities),
        fetch_inter_jobs(keywords, cities),
        fetch_c6bank_jobs(keywords, cities),
        fetch_itau_jobs(keywords, cities),
        fetch_santander_jobs(keywords, cities),
        return_exceptions=True,
    )

    valid_lists = [r for r in results if not isinstance(r, Exception)]
    combined = []
    for lst in valid_lists:
        combined.extend(lst)

    raw_jobs = _dedup_by_url(combined)
    raw_jobs = [j for j in raw_jobs if not _is_blocked(j.get("title", ""), blocked)]
    summary["scraped"] = len(raw_jobs)

    rate_limited = False

    with Session(engine) as session:
        for data in raw_jobs:
            try:
                if _url_exists(session, data["url"]):
                    continue

                lang = detect_language(data["title"], data.get("description", ""))
                job = _save_job(session, data, lang)

                if not job.email:
                    enriched = await enrich_email(job.url)
                    if enriched:
                        job.email = enriched
                        session.add(job)
                        session.commit()

                if not job.email:
                    continue

                summary["emails_found"] += 1

                if rate_limited:
                    continue

                subject, body = render_template(lang, {**_SENDER_VARS, "job_title": job.title, "company": job.company})

                sent = send_email(job.email, subject, body)

                if sent:
                    job.status = "sent"
                    job.sent_at = datetime.now(UTC)
                    session.add(job)
                    _log_email(session, job, subject, lang)
                    summary["sent"] += 1
                else:
                    _log_email(session, job, subject, lang, error="send_failed")
                    summary["errors"] += 1

            except RateLimitExceeded:
                logger.warning("Daily rate limit reached — stopping sends.")
                rate_limited = True

            except Exception as exc:
                logger.error("Pipeline error on job %s: %s", data.get("url"), exc)
                summary["errors"] += 1

    return summary


async def scrape_only_pipeline() -> list[Job]:
    keywords, cities = _load_config()
    blocked = _load_blocked()
    new_jobs: list[Job] = []

    results = await asyncio.gather(
        fetch_gupy_jobs(keywords, cities),
        fetch_google_jobs(keywords, cities),
        fetch_jooble_jobs(keywords, cities),
        fetch_remoteok_jobs(keywords, cities),
        fetch_adzuna_jobs(keywords, cities),
        fetch_arbeitnow_jobs(keywords, cities),
        fetch_programathor_jobs(keywords, cities),
        fetch_indeed_br_jobs(keywords, cities),
        fetch_amazon_jobs(keywords, cities),
        fetch_google_careers_jobs(keywords, cities),
        fetch_microsoft_careers_jobs(keywords, cities),
        fetch_meta_careers_jobs(keywords, cities),
        fetch_apple_careers_jobs(keywords, cities),
        fetch_netflix_jobs(keywords, cities),
        fetch_spotify_jobs(keywords, cities),
        fetch_uber_jobs(keywords, cities),
        fetch_airbnb_jobs(keywords, cities),
        fetch_salesforce_jobs(keywords, cities),
        fetch_sap_careers_jobs(keywords, cities),
        fetch_oracle_careers_jobs(keywords, cities),
        fetch_ibm_careers_jobs(keywords, cities),
        fetch_samsung_br_jobs(keywords, cities),
        fetch_dell_careers_jobs(keywords, cities),
        fetch_nubank_jobs(keywords, cities),
        fetch_ifood_jobs(keywords, cities),
        fetch_mercadolivre_jobs(keywords, cities),
        fetch_picpay_jobs(keywords, cities),
        fetch_stone_jobs(keywords, cities),
        fetch_rappi_jobs(keywords, cities),
        fetch_inter_jobs(keywords, cities),
        fetch_c6bank_jobs(keywords, cities),
        fetch_itau_jobs(keywords, cities),
        fetch_santander_jobs(keywords, cities),
        return_exceptions=True,
    )

    valid_lists = [r for r in results if not isinstance(r, Exception)]
    combined = []
    for lst in valid_lists:
        combined.extend(lst)

    raw_jobs = _dedup_by_url(combined)
    raw_jobs = [j for j in raw_jobs if not _is_blocked(j.get("title", ""), blocked)]

    with Session(engine) as session:
        for data in raw_jobs:
            try:
                if _url_exists(session, data["url"]):
                    continue
                lang = detect_language(data["title"], data.get("description", ""))
                job = _save_job(session, data, lang)

                if not job.email:
                    enriched = await enrich_email(job.url)
                    if enriched:
                        job.email = enriched
                        session.add(job)
                        session.commit()

                session.expunge(job)
                new_jobs.append(job)
            except Exception as exc:
                logger.error("scrape_only error on %s: %s", data.get("url"), exc)

    return new_jobs


def send_selected_jobs(job_ids: list[int]) -> dict[str, int]:
    """Send emails only for the given job IDs. Respects daily rate limit.

    Returns summary dict with sent/skipped/errors counts.
    """
    summary: dict[str, int] = {"sent": 0, "skipped": 0, "errors": 0}

    with Session(engine) as session:
        for job_id in job_ids:
            job = session.get(Job, job_id)
            if not job:
                summary["errors"] += 1
                continue

            if job.status == "sent":
                summary["skipped"] += 1
                continue

            if not job.email:
                summary["skipped"] += 1
                continue

            lang = job.language or "pt"
            try:
                subject, body = render_template(
                    lang,  # type: ignore[arg-type]
                    {**_SENDER_VARS, "job_title": job.title, "company": job.company},
                )
                sent = send_email(job.email, subject, body)
                if sent:
                    job.status = "sent"
                    job.sent_at = datetime.now(UTC)
                    session.add(job)
                    _log_email(session, job, subject, lang)
                    summary["sent"] += 1
                else:
                    _log_email(session, job, subject, lang, error="send_failed")
                    summary["errors"] += 1
            except RateLimitExceeded:
                logger.warning("Rate limit reached during send_selected.")
                summary["errors"] += 1
                break
            except Exception as exc:
                logger.error("send_selected error on job %s: %s", job_id, exc)
                summary["errors"] += 1

    return summary


def preview_job_email(job_id: int) -> tuple[str, str]:
    """Return (subject, body) for a job without sending.

    Raises ValueError if job not found.
    """
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        lang = job.language or "pt"
        subject, body = render_template(
            lang,  # type: ignore[arg-type]
            {**_SENDER_VARS, "job_title": job.title, "company": job.company},
        )
    return subject, body
