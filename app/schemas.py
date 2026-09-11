"""Typed API request and response contracts."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RunCreate(BaseModel):
    review_start_date: date = date(2026, 1, 1)
    review_end_date: date = date(2026, 6, 30)
    mapping_version: str = Field(default="DEMO_V1", min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_period(self):
        if self.review_start_date > self.review_end_date:
            raise ValueError("review_start_date must not be after review_end_date")
        return self


class RunView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: Literal["queued", "running", "completed", "failed"]
    review_start_date: date
    review_end_date: date
    mapping_version: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    comparison_count: int | None
    review_queue_count: int | None
    unmapped_code_count: int | None
    error_message: str | None


class ReviewView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_id: int
    patient_id: str
    patient_name: str
    condition_group: str
    submitted_codes: str
    documented_codes: str
    latest_claim_date: str
    latest_documentation_date: str
    submitted_present: bool
    documented_present: bool
    review_status: str
    review_reason: str
    workflow_status: Literal["pending", "in_review", "resolved"]
    reviewer_notes: str | None
    updated_at: datetime


class ReviewPage(BaseModel):
    items: list[ReviewView]
    total: int
    limit: int
    offset: int


class ReviewUpdate(BaseModel):
    workflow_status: Literal["pending", "in_review", "resolved"]
    reviewer_notes: str | None = Field(default=None, max_length=2000)


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody
