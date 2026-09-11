"""Command line entry point."""

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from .config import ReviewConfig
from .pipeline import ReviewPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run diagnosis reconciliation")
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument(
        "--start-date", type=date.fromisoformat, default=date(2026, 1, 1)
    )
    parser.add_argument(
        "--end-date", type=date.fromisoformat, default=date(2026, 6, 30)
    )
    parser.add_argument("--mapping-version", default="DEMO_V1")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = ReviewConfig(
        args.start_date,
        args.end_date,
        args.mapping_version,
        args.input_dir,
        args.output_dir,
    )
    outputs = ReviewPipeline(config).run()
    summary = {
        row["review_status"]: row["comparison_count"]
        for row in outputs["review_status_summary"]
    }
    logging.info("Pipeline completed %s", json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
