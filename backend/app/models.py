from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    company: str
    url: str
    description: Optional[str] = None
    email: Optional[str] = None
    language: Optional[str] = None  # "pt" | "en"
    status: str = Field(default="new")  # "new" | "sent" | "skipped"
    dismissed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None


class EmailLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    subject: str
    template_lang: str  # "pt" | "en"
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: Optional[str] = None
