# Sensor Data Quality Audit

A small, reproducible command-line audit for timestamped sensor CSV files. It reports missing and invalid values, duplicate timestamps, and gaps in the expected sampling cadence. It uses only the Python standard library and performs no automatic repair or network access.

## Input schema

CSV files must contain `timestamp` and `value` columns. Timestamps use ISO 8601 format; values must be numeric. The default expected interval is 60 seconds.

## Run

Requires Python 3.10 or newer. From this directory:

```sh
python -m src.quality_audit --demo
python -m src.quality_audit --input path/to/readings.csv --interval-seconds 60
cat path/to/readings.csv | python -m src.quality_audit
python -m unittest discover -s tests -v
```

The report is deterministic JSON written to stdout. Input errors are written to stderr and return exit code 2. The demo contains synthetic readings only.

## Interpretation

Quality flags describe structural issues in a file; they do not prove that a sensor failed, establish why a gap occurred, or make the readings suitable for a particular use. The audit never modifies input data. Gap counts are measured between distinct parseable timestamps; malformed timestamps are excluded from coverage calculations.
