import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    resume_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
