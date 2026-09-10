"""Configuration for a coding review run."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class ReviewConfig:
    """Validated settings shared by every pipeline stage."""

    review_start_date: date
    review_end_date: date
    mapping_version: str
    input_dir: Path
    output_dir: Path

    def __post_init__(self) -> None:
        if self.review_start_date > self.review_end_date:
            raise ValueError("review_start_date must not be after review_end_date")
        if not self.mapping_version.strip():
            raise ValueError("mapping_version must not be empty")

