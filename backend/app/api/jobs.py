"""Jobs API router — list and detail endpoints."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Job
from app.services.orchestrator import preview_job_email

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobRead(BaseModel):
    id: int
    title: str
    company: str
    url: str
    email: Optional[str]
    language: Optional[str]
    status: str
    created_at: str
    sent_at: Optional[str]

    model_config = {"from_attributes": True}


class EmailPreview(BaseModel):
    subject: str
    body: str


@router.get("", response_model=list[JobRead])
def list_jobs(
    status: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[Job]:
    query = select(Job)
    if status:
        query = query.where(Job.status == status)
    if language:
        query = query.where(Job.language == language)
    return list(session.exec(query.offset(offset).limit(limit)).all())


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, session: Session = Depends(get_session)) -> Job:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/preview", response_model=EmailPreview)
def get_email_preview(job_id: int) -> EmailPreview:
    """Return rendered email subject + body for the given job without sending."""
    try:
        subject, body = preview_job_email(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EmailPreview(subject=subject, body=body)

