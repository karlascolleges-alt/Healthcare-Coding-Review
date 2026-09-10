import sys
from pathlib import Path

from coding_review import cli


def test_cli_runs_complete_pipeline(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]

    monkeypatch.chdir(root)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-review",
            "--input-dir",
            str(root / "data" / "raw"),
            "--output-dir",
            str(tmp_path),
            "--start-date",
            "2026-01-01",
            "--end-date",
            "2026-06-30",
            "--mapping-version",
            "DEMO_V1",
        ],
    )

    cli.main()

    expected_files = {
        "coding_review_results.csv",
        "human_review_queue.csv",
        "review_status_summary.csv",
        "unmapped_codes.csv",
        "run_audit.csv",
    }

    assert {path.name for path in tmp_path.glob("*.csv")} == expected_files
