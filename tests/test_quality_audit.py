import io
import json
import unittest

from src.quality_audit import audit_csv, demo_csv, main


class QualityAuditTests(unittest.TestCase):
    def test_clean_csv_has_no_issues(self):
        result = audit_csv(io.StringIO("timestamp,value\n2025-01-01T00:00:00Z,2\n2025-01-01T00:01:00Z,3\n"))
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["issue_counts"], {"missing_values": 0, "invalid_values": 0, "duplicate_timestamps": 0, "sampling_gaps": 0})

    def test_counts_missing_invalid_duplicate_and_gap(self):
        csv = "timestamp,value\n2025-01-01T00:00:00Z,1\n2025-01-01T00:00:00Z,nope\n2025-01-01T00:03:00Z,\n"
        result = audit_csv(io.StringIO(csv), expected_interval_seconds=60)
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["issue_counts"], {"missing_values": 1, "invalid_values": 1, "duplicate_timestamps": 1, "sampling_gaps": 2})
        self.assertEqual(result["valid_value_count"], 1)

    def test_rejects_missing_schema(self):
        with self.assertRaisesRegex(ValueError, "timestamp.*value"):
            audit_csv(io.StringIO("time,reading\nnow,1\n"))

    def test_demo_cli_is_deterministic_json(self):
        first, second = io.StringIO(), io.StringIO()
        self.assertEqual(main(["--demo"], stdout=first), 0)
        self.assertEqual(main(["--demo"], stdout=second), 0)
        self.assertEqual(first.getvalue(), second.getvalue())
        self.assertEqual(json.loads(first.getvalue())["row_count"], 5)


if __name__ == "__main__":
    unittest.main()
