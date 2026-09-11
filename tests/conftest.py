from datetime import date
from pathlib import Path

import pytest

from coding_review.config import ReviewConfig


@pytest.fixture
def config(tmp_path: Path) -> ReviewConfig:
    root = Path(__file__).resolve().parents[1]
    return ReviewConfig(
        date(2026, 1, 1), date(2026, 6, 30), "DEMO_V1", root / "data/raw", tmp_path
    )
