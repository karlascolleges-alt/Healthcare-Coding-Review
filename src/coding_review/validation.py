"""Input contracts and relationship validation."""

from collections import Counter

from .exceptions import DataValidationError


REQUIRED_COLUMNS = {
    "patients": {"patient_id", "patient_name"},
    "claims": {"claim_id", "patient_id", "service_date", "claim_status"},
    "claim_diagnoses": {"claim_diagnosis_id", "claim_id", "diagnosis_code"},
    "documented_diagnoses": {
        "documented_diagnosis_id",
        "patient_id",
        "documentation_date",
        "diagnosis_code",
    },
    "diagnosis_mapping": {
        "mapping_version",
        "diagnosis_code",
        "diagnosis_name",
        "demo_condition_group",
        "active_flag",
    },
}


def validate_columns(name: str, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise DataValidationError(f"{name} must contain at least one record")
    missing = REQUIRED_COLUMNS[name] - set(rows[0])
    if missing:
        raise DataValidationError(f"{name} is missing columns: {sorted(missing)}")


def validate_unique(name: str, rows: list[dict[str, str]], key: str) -> None:
    counts = Counter(row[key] for row in rows)
    duplicates = sorted(value for value, count in counts.items() if count > 1)
    if duplicates:
        raise DataValidationError(f"{name}.{key} contains duplicates: {duplicates}")


def validate_relationships(datasets: dict[str, list[dict[str, str]]]) -> None:
    patient_ids = {row["patient_id"] for row in datasets["patients"]}
    claim_ids = {row["claim_id"] for row in datasets["claims"]}
    orphan_claims = {
        row["claim_id"]
        for row in datasets["claims"]
        if row["patient_id"] not in patient_ids
    }
    orphan_claim_diagnoses = {
        row["claim_diagnosis_id"]
        for row in datasets["claim_diagnoses"]
        if row["claim_id"] not in claim_ids
    }
    orphan_documentation = {
        row["documented_diagnosis_id"]
        for row in datasets["documented_diagnoses"]
        if row["patient_id"] not in patient_ids
    }
    if orphan_claims or orphan_claim_diagnoses or orphan_documentation:
        raise DataValidationError(
            "orphan records found: "
            f"claims={sorted(orphan_claims)}, "
            f"claim_diagnoses={sorted(orphan_claim_diagnoses)}, "
            f"documentation={sorted(orphan_documentation)}"
        )
