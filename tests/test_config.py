from datetime import date
from pathlib import Path

import pytest

from coding_review.config import ReviewConfig


def test_rejects_reversed_date_range():
    with pytest.raises(ValueError, match="must not be after"):
        ReviewConfig(
            date(2026, 2, 1),
            date(2026, 1, 1),
            "DEMO_V1",
            Path("in"),
            Path("out"),
        )


def test_rejects_blank_mapping_version():
    with pytest.raises(ValueError, match="must not be empty"):
        ReviewConfig(date(2026, 1, 1), date(2026, 2, 1), " ", Path("in"), Path("out"))
