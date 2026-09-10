"""Reproducible diagnosis reconciliation pipeline."""

from collections import Counter, defaultdict
from datetime import UTC, date, datetime

from .config import ReviewConfig
from .io import read_csv, write_csv_atomic
from .validation import validate_columns, validate_relationships, validate_unique

CAPTURED = "Captured"
POTENTIAL_GAP = "Potential Gap Review Required"
DOCUMENTATION_REVIEW = "Submitted Code Documentation Review Required"


class ReviewPipeline:
    """Load, validate, reconcile, explain, and export coding review results."""

    filenames = {
        "patients": "patients.csv",
        "claims": "claims.csv",
        "claim_diagnoses": "claim_diagnoses.csv",
        "documented_diagnoses": "documented_diagnoses.csv",
        "diagnosis_mapping": "diagnosis_mapping.csv",
    }

    def __init__(self, config: ReviewConfig) -> None:
        self.config = config
        self.datasets: dict[str, list[dict[str, str]]] = {}

    def load(self) -> "ReviewPipeline":
        self.datasets = {
            name: read_csv(self.config.input_dir / filename)
            for name, filename in self.filenames.items()
        }
        return self

    def validate(self) -> "ReviewPipeline":
        for name, rows in self.datasets.items():
            validate_columns(name, rows)
        validate_unique("patients", self.datasets["patients"], "patient_id")
        validate_unique("claims", self.datasets["claims"], "claim_id")
        validate_unique(
            "claim_diagnoses",
            self.datasets["claim_diagnoses"],
            "claim_diagnosis_id",
        )
        validate_unique(
            "documented_diagnoses",
            self.datasets["documented_diagnoses"],
            "documented_diagnosis_id",
        )
        validate_relationships(self.datasets)
        return self

    def run(self) -> dict[str, list[dict[str, object]]]:
        if not self.datasets:
            self.load()
        self.validate()

        mappings = {
            row["diagnosis_code"]: row["demo_condition_group"]
            for row in self.datasets["diagnosis_mapping"]
            if row["mapping_version"] == self.config.mapping_version
            and row["active_flag"].lower() == "true"
        }
        claims = {row["claim_id"]: row for row in self.datasets["claims"]}
        submitted, unmapped_submitted = self._submitted_groups(claims, mappings)
        documented, unmapped_documented = self._documented_groups(mappings)
        comparisons = self._compare(submitted, documented)
        queue = [row for row in comparisons if row["review_status"] != CAPTURED]
        summary_counts = Counter(row["review_status"] for row in comparisons)
        summary = [
            {"review_status": status, "comparison_count": summary_counts[status]}
            for status in (CAPTURED, POTENTIAL_GAP, DOCUMENTATION_REVIEW)
        ]
        unmapped = self._unmapped_rows(unmapped_submitted, unmapped_documented)
        audit = [
            {
                "run_id": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
                "review_start_date": self.config.review_start_date.isoformat(),
                "review_end_date": self.config.review_end_date.isoformat(),
                "mapping_version": self.config.mapping_version,
                "comparison_count": len(comparisons),
                "review_queue_count": len(queue),
                "unmapped_code_count": sum(
                    int(row["occurrence_count"]) for row in unmapped
                ),
            }
        ]
        outputs = {
            "coding_review_results": comparisons,
            "human_review_queue": queue,
            "review_status_summary": summary,
            "unmapped_codes": unmapped,
            "run_audit": audit,
        }
        self._write(outputs)
        return outputs

    def _in_period(self, value: str) -> bool:
        parsed = date.fromisoformat(value)
        return self.config.review_start_date <= parsed <= self.config.review_end_date

    def _submitted_groups(self, claims, mappings):
        groups: dict[tuple[str, str], dict[str, object]] = defaultdict(
            lambda: {"codes": set(), "dates": []}
        )
        unmapped: Counter[str] = Counter()
        for diagnosis in self.datasets["claim_diagnoses"]:
            claim = claims[diagnosis["claim_id"]]
            if claim["claim_status"] != "Submitted" or not self._in_period(
                claim["service_date"]
            ):
                continue
            code = diagnosis["diagnosis_code"]
            group = mappings.get(code)
            if group is None:
                unmapped[code] += 1
                continue
            item = groups[(claim["patient_id"], group)]
            item["codes"].add(code)
            item["dates"].append(claim["service_date"])
        return groups, unmapped

    def _documented_groups(self, mappings):
        groups: dict[tuple[str, str], dict[str, object]] = defaultdict(
            lambda: {"codes": set(), "dates": []}
        )
        unmapped: Counter[str] = Counter()
        for diagnosis in self.datasets["documented_diagnoses"]:
            if not self._in_period(diagnosis["documentation_date"]):
                continue
            code = diagnosis["diagnosis_code"]
            group = mappings.get(code)
            if group is None:
                unmapped[code] += 1
                continue
            item = groups[(diagnosis["patient_id"], group)]
            item["codes"].add(code)
            item["dates"].append(diagnosis["documentation_date"])
        return groups, unmapped

    def _compare(self, submitted, documented):
        patients = {
            row["patient_id"]: row["patient_name"]
            for row in self.datasets["patients"]
        }
        results = []
        for patient_id, group in sorted(set(submitted) | set(documented)):
            submitted_item = submitted.get((patient_id, group))
            documented_item = documented.get((patient_id, group))
            submitted_present = submitted_item is not None
            documented_present = documented_item is not None
            if submitted_present and documented_present:
                status = CAPTURED
                reason = (
                    "Condition group appears in both submitted claims "
                    "and documentation"
                )
            elif documented_present:
                status = POTENTIAL_GAP
                reason = (
                    "Documented condition group is absent from submitted claims "
                    "in the review period"
                )
            else:
                status = DOCUMENTATION_REVIEW
                reason = (
                    "Submitted condition group is absent from documentation "
                    "in the review period"
                )
            results.append({
                "patient_id": patient_id,
                "patient_name": patients[patient_id],
                "demo_condition_group": group,
                "submitted_codes": self._codes(submitted_item),
                "documented_codes": self._codes(documented_item),
                "latest_claim_date": self._latest(submitted_item),
                "latest_documentation_date": self._latest(documented_item),
                "submitted_present": submitted_present,
                "documented_present": documented_present,
                "review_status": status,
                "review_reason": reason,
            })
        return results

    @staticmethod
    def _codes(item):
        return ", ".join(sorted(item["codes"])) if item else ""

    @staticmethod
    def _latest(item):
        return max(item["dates"]) if item else ""

    @staticmethod
    def _unmapped_rows(submitted, documented):
        return [
            {"source_name": source, "diagnosis_code": code, "occurrence_count": count}
            for source, counter in (
                ("DOCUMENTATION", documented),
                ("SUBMITTED_CLAIM", submitted),
            )
            for code, count in sorted(counter.items())
        ]

    def _write(self, outputs):
        for name, rows in outputs.items():
            if rows:
                write_csv_atomic(
                    self.config.output_dir / f"{name}.csv",
                    rows,
                    list(rows[0]),
                )
