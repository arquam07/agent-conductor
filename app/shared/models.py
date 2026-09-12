"""Data models: the job row (DB) and the API request/response schemas."""
import enum
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    """One agentic job. Written by API (queued), updated by worker."""
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    task: Mapped[str] = mapped_column(Text)  # the agent task prompt
    params: Mapped[str] = mapped_column(Text, default="{}")  # JSON string
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


# ---- API schemas ----

class JobRequest(BaseModel):
    task: str
    params: dict = {}


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobDetail(BaseModel):
    job_id: str
    status: JobStatus
    task: str
    result: str | None = None
    error: str | None = None