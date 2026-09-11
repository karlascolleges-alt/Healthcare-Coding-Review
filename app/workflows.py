"""Run the domain pipeline and persist its workflow state."""

import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from coding_review.config import ReviewConfig
from coding_review.pipeline import ReviewPipeline

from .database import PipelineRun, ReviewRecord

LOGGER = logging.getLogger("coding_review.workflow")


def execute_run(run_id: int, session_factory, root: Path) -> None:
    with session_factory() as session:
        run = session.get(PipelineRun, run_id)
        if run is None:
            LOGGER.error("run_not_found", extra={"run_id": run_id})
            return
        run.status = "running"
        run.started_at = datetime.now(UTC)
        session.commit()
        try:
            config = ReviewConfig(
                run.review_start_date,
                run.review_end_date,
                run.mapping_version,
                root / "data" / "raw",
                root / "data" / "processed",
            )
            outputs = ReviewPipeline(config).run()
            _persist_results(session, run, outputs)
            LOGGER.info("run_completed", extra={"run_id": run.id})
        except Exception as exc:
            session.rollback()
            failed_run = session.get(PipelineRun, run_id)
            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.completed_at = datetime.now(UTC)
                failed_run.error_message = str(exc)[:2000]
                session.commit()
            LOGGER.exception("run_failed", extra={"run_id": run_id})


def _persist_results(session: Session, run: PipelineRun, outputs: dict) -> None:
    now = datetime.now(UTC)
    for row in outputs["coding_review_results"]:
        session.add(
            ReviewRecord(
                run_id=run.id,
                patient_id=str(row["patient_id"]),
                patient_name=str(row["patient_name"]),
                condition_group=str(row["demo_condition_group"]),
                submitted_codes=str(row["submitted_codes"]),
                documented_codes=str(row["documented_codes"]),
                latest_claim_date=str(row["latest_claim_date"]),
                latest_documentation_date=str(row["latest_documentation_date"]),
                submitted_present=bool(row["submitted_present"]),
                documented_present=bool(row["documented_present"]),
                review_status=str(row["review_status"]),
                review_reason=str(row["review_reason"]),
                workflow_status="pending",
                updated_at=now,
            )
        )
    audit = outputs["run_audit"][0]
    run.status = "completed"
    run.completed_at = now
    run.comparison_count = int(audit["comparison_count"])
    run.review_queue_count = int(audit["review_queue_count"])
    run.unmapped_code_count = int(audit["unmapped_code_count"])
    session.commit()
