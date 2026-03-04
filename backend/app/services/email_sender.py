"""Gmail API email sender — enforces 30/day hard limit via EmailLog."""

import base64
import logging
import os
from datetime import date
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlmodel import Session, func, select

from app.database import engine
from app.models import EmailLog

logger = logging.getLogger(__name__)

DAILY_LIMIT = 30


class RateLimitExceeded(Exception):
    """Raised when the daily email limit has been reached."""


def get_gmail_service():  # type: ignore[return]
    """Build an authenticated Gmail API service from env vars.

    Never logs token values.
    """
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    return build("gmail", "v1", credentials=creds)


def _get_today_sent_count(session: Session) -> int:
    result = session.exec(
        select(func.count(EmailLog.id)).where(
            func.date(EmailLog.sent_at) == date.today()
        )
    ).one()
    return result or 0


def _build_message(to: str, subject: str, body: str) -> dict[str, dict[str, str]]:
    mime = MIMEText(body, "plain", "utf-8")
    mime["to"] = to
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    return {"raw": raw}


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email via Gmail API. Returns True on success, False on failure.

    Raises RateLimitExceeded if today's count >= DAILY_LIMIT.
    Never uses SMTP. Never logs token values.
    """
    with Session(engine) as session:
        count = _get_today_sent_count(session)
        if count >= DAILY_LIMIT:
            raise RateLimitExceeded(
                f"Daily limit of {DAILY_LIMIT} emails reached ({count} sent today)."
            )

    try:
        service = get_gmail_service()
        message = _build_message(to, subject, body)
        service.users().messages().send(userId="me", body=message).execute()
        logger.info("Email sent to %s | subject: %s", to, subject)
        return True
    except HttpError as exc:
        logger.error("Gmail API error sending to %s: %s", to, exc)
        return False
    except Exception as exc:
        logger.error("Unexpected error sending to %s: %s", to, exc)
        return False
