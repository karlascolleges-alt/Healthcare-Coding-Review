"""Database-backed workflow API for healthcare coding review."""

import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import PipelineRun, ReviewRecord, build_session_factory
from .schemas import (
    ErrorResponse,
    ReviewPage,
    ReviewUpdate,
    ReviewView,
    RunCreate,
    RunView,
)
from .workflows import execute_run

ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger("coding_review.api")


def create_app(database_url: str | None = None, root: Path = ROOT) -> FastAPI:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    session_factory = build_session_factory(database_url)
    application = FastAPI(
        title="Healthcare Coding Review Workflow API",
        version="2.0.0",
        description=(
            "Runs diagnosis reconciliation and persists auditable review workflows."
        ),
    )

    def get_session():
        with session_factory() as session:
            yield session

    @application.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        detail = exc.detail
        error = (
            detail
            if isinstance(detail, dict)
            else {"code": "http_error", "message": str(detail)}
        )
        return JSONResponse(status_code=exc.status_code, content={"error": error})

    @application.get("/health")
    def health(session: Session = Depends(get_session)) -> dict[str, str]:
        session.execute(select(1))
        return {"status": "healthy", "database": "connected"}

    @application.post(
        "/runs",
        response_model=RunView,
        status_code=202,
        responses={422: {"model": ErrorResponse}},
    )
    def start_run(
        payload: RunCreate,
        tasks: BackgroundTasks,
        session: Session = Depends(get_session),
    ) -> PipelineRun:
        run = PipelineRun(
            status="queued",
            review_start_date=payload.review_start_date,
            review_end_date=payload.review_end_date,
            mapping_version=payload.mapping_version.strip(),
            created_at=datetime.now(UTC),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        tasks.add_task(execute_run, run.id, session_factory, root)
        LOGGER.info("run_queued", extra={"run_id": run.id})
        return run

    @application.get("/runs/{run_id}", response_model=RunView)
    def get_run(run_id: int, session: Session = Depends(get_session)) -> PipelineRun:
        run = session.get(PipelineRun, run_id)
        if run is None:
            raise HTTPException(
                404,
                detail={
                    "code": "run_not_found",
                    "message": "Pipeline run was not found",
                },
            )
        return run

    @application.get("/reviews", response_model=ReviewPage)
    def list_reviews(
        run_id: int | None = None,
        review_status: str | None = None,
        workflow_status: str | None = None,
        patient_id: str | None = None,
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
        session: Session = Depends(get_session),
    ) -> ReviewPage:
        filters = []
        if run_id is not None:
            filters.append(ReviewRecord.run_id == run_id)
        if review_status:
            filters.append(ReviewRecord.review_status == review_status)
        if workflow_status:
            filters.append(ReviewRecord.workflow_status == workflow_status)
        if patient_id:
            filters.append(ReviewRecord.patient_id == patient_id)
        total = (
            session.scalar(
                select(func.count()).select_from(ReviewRecord).where(*filters)
            )
            or 0
        )
        items = session.scalars(
            select(ReviewRecord)
            .where(*filters)
            .order_by(ReviewRecord.id)
            .offset(offset)
            .limit(limit)
        ).all()
        return ReviewPage(items=list(items), total=total, limit=limit, offset=offset)

    @application.patch("/reviews/{review_id}", response_model=ReviewView)
    def update_review(
        review_id: int, payload: ReviewUpdate, session: Session = Depends(get_session)
    ) -> ReviewRecord:
        review = session.get(ReviewRecord, review_id)
        if review is None:
            raise HTTPException(
                404,
                detail={
                    "code": "review_not_found",
                    "message": "Review record was not found",
                },
            )
        review.workflow_status = payload.workflow_status
        review.reviewer_notes = payload.reviewer_notes
        review.updated_at = datetime.now(UTC)
        session.commit()
        session.refresh(review)
        LOGGER.info(
            "review_updated", extra={"review_id": review.id, "run_id": review.run_id}
        )
        return review

    return application


app = create_app()
