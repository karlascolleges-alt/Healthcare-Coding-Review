"""Read only API for review results."""

import csv
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
app = FastAPI(title="Healthcare Coding Review API", version="1.0.0")


def load(name: str) -> list[dict[str, str]]:
    path = DATA / name
    if not path.exists():
        raise HTTPException(status_code=503, detail="Pipeline output is unavailable")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/reviews")
def reviews(
    status: str | None = None,
    patient_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict[str, str]]:
    rows = load("coding_review_results.csv")
    if status:
        rows = [row for row in rows if row["review_status"] == status]
    if patient_id:
        rows = [row for row in rows if row["patient_id"] == patient_id]
    return rows[:limit]


@app.get("/summary")
def summary() -> list[dict[str, str]]:
    return load("review_status_summary.csv")
