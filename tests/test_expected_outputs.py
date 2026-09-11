import csv
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ExpectedOutputTests(unittest.TestCase):
    def test_summary_matches_expected_counts(self):
        path = ROOT / "sample_output" / "review_status_summary.csv"

        with path.open(newline="", encoding="utf-8") as handle:
            counts = {
                row["review_status"]: int(row["comparison_count"])
                for row in csv.DictReader(handle)
            }

        self.assertEqual(sum(counts.values()), 14)
        self.assertEqual(counts["Captured"], 9)
        self.assertEqual(
            counts["Potential Gap Review Required"],
            3,
        )
        self.assertEqual(
            counts["Submitted Code Documentation Review Required"],
            2,
        )

    def test_human_queue_contains_five_unique_groups(self):
        path = ROOT / "sample_output" / "human_review_queue.csv"

        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        keys = {
            (
                row["patient_id"],
                row["demo_condition_group"],
            )
            for row in rows
        }

        self.assertEqual(len(rows), 5)
        self.assertEqual(len(keys), 5)

    def test_unmapped_codes_remain_visible(self):
        path = ROOT / "sample_output" / "unmapped_codes.csv"

        with path.open(newline="", encoding="utf-8") as handle:
            codes = {
                (
                    row["source_name"],
                    row["diagnosis_code"],
                )
                for row in csv.DictReader(handle)
            }

        self.assertEqual(
            codes,
            {
                ("DOCUMENTATION", "E78.5"),
                ("SUBMITTED_CLAIM", "Z00.00"),
            },
        )


if __name__ == "__main__":
    unittest.main()
