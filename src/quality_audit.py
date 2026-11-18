"""Deterministic quality checks for timestamped sensor CSV files."""

import argparse
import csv
import json
import sys
from datetime import datetime


def _parse_timestamp(value):
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        return None


def audit_csv(stream, expected_interval_seconds=60):
    if expected_interval_seconds <= 0:
        raise ValueError("expected interval must be positive")
    reader = csv.DictReader(stream)
    if not reader.fieldnames or not {"timestamp", "value"}.issubset(reader.fieldnames):
        raise ValueError("CSV must contain timestamp and value columns")

    rows = list(reader)
    timestamps, valid_values = [], 0
    missing = invalid = 0
    for row in rows:
        timestamp = (row.get("timestamp") or "").strip()
        value = (row.get("value") or "").strip()
        if not timestamp or not value:
            missing += 1
        try:
            float(value)
            valid_values += 1
        except ValueError:
            if value:
                invalid += 1
        parsed = _parse_timestamp(timestamp)
        if parsed is not None:
            timestamps.append(parsed)

    unique_sorted = sorted(set(timestamps))
    gaps = sum(
        max(0, int((current - previous).total_seconds() // expected_interval_seconds) - 1)
        for previous, current in zip(unique_sorted, unique_sorted[1:])
    )
    duplicate_count = len(timestamps) - len(set(timestamps))
    return {
        "row_count": len(rows),
        "valid_value_count": valid_values,
        "issue_counts": {
            "missing_values": missing,
            "invalid_values": invalid,
            "duplicate_timestamps": duplicate_count,
            "sampling_gaps": gaps,
        },
        "timestamp_coverage": {
            "start": unique_sorted[0].isoformat() if unique_sorted else None,
            "end": unique_sorted[-1].isoformat() if unique_sorted else None,
            "expected_interval_seconds": expected_interval_seconds,
        },
        "limitations": "Flags describe input quality only; they do not establish sensor failure or repair data.",
    }


def demo_csv():
    return "timestamp,value\n2025-01-01T00:00:00Z,21.4\n2025-01-01T00:01:00Z,21.5\n2025-01-01T00:02:00Z,\n2025-01-01T00:02:00Z,invalid\n2025-01-01T00:05:00Z,22.0\n"


def main(argv=None, stdout=None):
    parser = argparse.ArgumentParser(description="Audit timestamped sensor CSV data.")
    parser.add_argument("--input", help="CSV path; defaults to stdin")
    parser.add_argument("--demo", action="store_true", help="audit the built-in synthetic example")
    parser.add_argument("--interval-seconds", type=int, default=60, help="expected sampling interval")
    args = parser.parse_args(argv)
    output = stdout or sys.stdout
    try:
        if args.demo and args.input:
            raise ValueError("choose either --demo or --input")
        if args.demo:
            result = audit_csv(__import__("io").StringIO(demo_csv()), args.interval_seconds)
        elif args.input:
            with open(args.input, newline="", encoding="utf-8") as stream:
                result = audit_csv(stream, args.interval_seconds)
        else:
            result = audit_csv(sys.stdin, args.interval_seconds)
        output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return 0
    except (OSError, ValueError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
