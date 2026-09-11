import pytest

from coding_review.exceptions import DataValidationError
from coding_review.validation import validate_columns, validate_unique


def test_rejects_missing_required_column():
    with pytest.raises(DataValidationError, match="missing columns"):
        validate_columns("patients", [{"patient_id": "1"}])


def test_rejects_duplicate_primary_key():
    rows = [{"patient_id": "1"}, {"patient_id": "1"}]
    with pytest.raises(DataValidationError, match="duplicates"):
        validate_unique("patients", rows, "patient_id")
