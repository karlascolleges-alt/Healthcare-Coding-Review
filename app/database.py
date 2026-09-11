"""Database models and session management for workflow state."""

from __future__ import annotations

import os
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)


class Base(DeclarativeBase):
    pass


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default="queued")
    review_start_date: Mapped[date] = mapped_column(Date)
    review_end_date: Mapped[date] = mapped_column(Date)
    mapping_version: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    comparison_count: Mapped[int | None] = mapped_column(Integer)
    review_queue_count: Mapped[int | None] = mapped_column(Integer)
    unmapped_code_count: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    reviews: Mapped[list[ReviewRecord]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)
    patient_id: Mapped[str] = mapped_column(String(80), index=True)
    patient_name: Mapped[str] = mapped_column(String(200))
    condition_group: Mapped[str] = mapped_column(String(120), index=True)
    submitted_codes: Mapped[str] = mapped_column(Text, default="")
    documented_codes: Mapped[str] = mapped_column(Text, default="")
    latest_claim_date: Mapped[str] = mapped_column(String(10), default="")
    latest_documentation_date: Mapped[str] = mapped_column(String(10), default="")
    submitted_present: Mapped[bool] = mapped_column(Boolean)
    documented_present: Mapped[bool] = mapped_column(Boolean)
    review_status: Mapped[str] = mapped_column(String(100), index=True)
    review_reason: Mapped[str] = mapped_column(Text)
    workflow_status: Mapped[str] = mapped_column(
        String(20), index=True, default="pending"
    )
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    run: Mapped[PipelineRun] = relationship(back_populates="reviews")


def build_session_factory(database_url: str | None = None):
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./data/coding_review.db")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
