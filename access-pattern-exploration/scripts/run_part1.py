"""Reproduce the Part 1 report from a cached extraction directory.

Usage:
    python scripts/run_part1.py [data_dir] [out_dir]

Defaults to the 10,000-block pilot extraction and reports/part1_pilot/. See the top-level
README for how to extract a different (e.g. the full frozen 1,000,000-block) range first.
"""

from __future__ import annotations

import sys
from pathlib import Path

from apx.pipeline import build_results_table, validation_summary
from apx.report import build_report

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "data" / "pilot_10k"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / "reports" / "part1_pilot"

    results = build_results_table(data_dir)
    validation = validation_summary(data_dir)

    report_path = build_report(results, validation, out_dir)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
