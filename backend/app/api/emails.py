"""Emails API router — log list and stats endpoints."""

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.database import get_session
from app.dependencies.auth import require_api_key
from app.models import EmailLog

router = APIRouter(
    prefix="/api/emails",
    tags=["emails"],
    dependencies=[Depends(require_api_key)],
)


class EmailLogRead(BaseModel):
    id: int
    job_id: int
    subject: str
    template_lang: str
    sent_at: str
    error_message: str | None

    model_config = {"from_attributes": True}


class EmailStats(BaseModel):
    total_sent_today: int
    total_sent_all: int
    errors_today: int


@router.get("", response_model=list[EmailLogRead])
def list_email_logs(
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> list[EmailLog]:
    return list(
        session.exec(select(EmailLog).offset(offset).limit(limit)).all()
    )


@router.get("/stats", response_model=EmailStats)
def email_stats(session: Session = Depends(get_session)) -> EmailStats:
    today = date.today()

    total_sent_today = session.exec(
        select(func.count(EmailLog.id)).where(
            func.date(EmailLog.sent_at) == today,
            EmailLog.error_message.is_(None),  # type: ignore[union-attr]
        )
    ).one() or 0

    total_sent_all = session.exec(
        select(func.count(EmailLog.id)).where(
            EmailLog.error_message.is_(None)  # type: ignore[union-attr]
        )
    ).one() or 0

    errors_today = session.exec(
        select(func.count(EmailLog.id)).where(
            func.date(EmailLog.sent_at) == today,
            EmailLog.error_message.isnot(None),  # type: ignore[union-attr]
        )
    ).one() or 0

    return EmailStats(
        total_sent_today=total_sent_today,
        total_sent_all=total_sent_all,
        errors_today=errors_today,
    )
