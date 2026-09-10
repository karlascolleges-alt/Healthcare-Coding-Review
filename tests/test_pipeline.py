import csv

from coding_review.pipeline import (
    CAPTURED,
    DOCUMENTATION_REVIEW,
    POTENTIAL_GAP,
    ReviewPipeline,
)


def run(config):
    return ReviewPipeline(config).load().validate().run()


def test_expected_status_counts(config):
    output = run(config)
    counts = {
        row["review_status"]: row["comparison_count"]
        for row in output["review_status_summary"]
    }
    assert counts == {CAPTURED: 9, POTENTIAL_GAP: 3, DOCUMENTATION_REVIEW: 2}


def test_review_queue_has_five_unique_groups(config):
    queue = run(config)["human_review_queue"]
    assert len(queue) == 5
    assert len({(row["patient_id"], row["demo_condition_group"]) for row in queue}) == 5


def test_unmapped_codes_remain_visible(config):
    unmapped = run(config)["unmapped_codes"]
    actual = {
        (row["source_name"], row["diagnosis_code"], row["occurrence_count"])
        for row in unmapped
    }
    assert actual == {
        ("DOCUMENTATION", "E78.5", 2),
        ("SUBMITTED_CLAIM", "Z00.00", 1),
    }


def test_voided_claim_is_excluded(config):
    results = run(config)["coding_review_results"]
    patient_ten = [row for row in results if row["patient_id"] == "10"]
    assert patient_ten == []


def test_out_of_period_records_are_excluded(config):
    results = run(config)["coding_review_results"]
    patient_two_groups = {
        row["demo_condition_group"]
        for row in results
        if row["patient_id"] == "2"
    }
    assert patient_two_groups == {"DEMO_DIABETES"}


def test_duplicate_evidence_does_not_duplicate_result(config):
    results = run(config)["coding_review_results"]
    matches = [
        row
        for row in results
        if row["patient_id"] == "1"
        and row["demo_condition_group"] == "DEMO_CARDIOVASCULAR"
    ]
    assert len(matches) == 1
    assert matches[0]["submitted_codes"] == "I10"


def test_output_files_are_written(config):
    run(config)
    expected = {
        "coding_review_results.csv",
        "human_review_queue.csv",
        "review_status_summary.csv",
        "unmapped_codes.csv",
        "run_audit.csv",
    }
    assert {path.name for path in config.output_dir.glob("*.csv")} == expected
    with (config.output_dir / "run_audit.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        audit = next(csv.DictReader(handle))
    assert audit["comparison_count"] == "14"
    assert audit["review_queue_count"] == "5"
