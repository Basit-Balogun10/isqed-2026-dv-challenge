#!/usr/bin/env python3
"""Task 3.1 log parser and analysis validator.

This utility provides two helper modes:
1) Extract UVM_ERROR context from a raw log file.
2) Validate the expected Task 3.1 analysis YAML files are present and structurally complete.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


REQUIRED_KEYS = (
    "failure_id:",
    "classification:",
    "root_module:",
    "root_line_range:",
    "root_cause:",
    "suggested_fix:",
    "confidence:",
)


def extract_error_context(log_path: pathlib.Path, context: int) -> int:
    if not log_path.is_file():
        print(f"[FAIL] Missing log file: {log_path}", file=sys.stderr)
        return 1

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = [idx for idx, line in enumerate(lines) if "UVM_ERROR" in line]
    if not hits:
        print("[INFO] No UVM_ERROR lines found")
        return 0

    print(f"[INFO] Found {len(hits)} UVM_ERROR line(s) in {log_path.name}")
    for n, idx in enumerate(hits, start=1):
        start = max(0, idx - context)
        end = min(len(lines), idx + context + 1)
        print(f"\n--- Error {n} (line {idx + 1}) ---")
        for ln in range(start, end):
            marker = ">" if ln == idx else " "
            print(f"{marker} {ln + 1:5d}: {lines[ln]}")
    return 0


def validate_analysis(analysis_dir: pathlib.Path) -> int:
    if not analysis_dir.is_dir():
        print(f"[FAIL] Analysis directory missing: {analysis_dir}", file=sys.stderr)
        return 1

    failures: list[str] = []

    for idx in range(1, 11):
        file_name = f"failure_{idx:02d}.yaml"
        file_path = analysis_dir / file_name
        if not file_path.is_file():
            failures.append(f"Missing file: {file_name}")
            continue

        text = file_path.read_text(encoding="utf-8", errors="replace")
        for key in REQUIRED_KEYS:
            if key not in text:
                failures.append(f"{file_name}: missing key '{key[:-1]}'")

        id_match = re.search(r"^failure_id:\s*(\d+)\s*$", text, flags=re.MULTILINE)
        if not id_match:
            failures.append(f"{file_name}: failure_id missing or not integer")
        elif int(id_match.group(1)) != idx:
            failures.append(f"{file_name}: failure_id mismatch (expected {idx})")

        class_match = re.search(
            r'^classification:\s*"(functional_bug|testbench_bug|protocol_violation|timing_issue|configuration_error)"\s*$',
            text,
            flags=re.MULTILINE,
        )
        if not class_match:
            failures.append(f"{file_name}: invalid classification value")

        confidence_match = re.search(r"^confidence:\s*([0-9]*\.?[0-9]+)\s*$", text, flags=re.MULTILINE)
        if not confidence_match:
            failures.append(f"{file_name}: confidence missing or not numeric")
        else:
            value = float(confidence_match.group(1))
            if value < 0.0 or value > 1.0:
                failures.append(f"{file_name}: confidence must be in [0.0, 1.0]")

    if failures:
        print("[FAIL] Analysis validation failed:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("[OK] Analysis validation passed for failure_01..failure_10")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 3.1 log parser and validator")
    parser.add_argument("--log", type=pathlib.Path, help="Path to a failure log for error-context extraction")
    parser.add_argument("--context", type=int, default=3, help="Context lines before/after each UVM_ERROR")
    parser.add_argument("--validate", type=pathlib.Path, help="Validate Task 3.1 analysis YAML directory")

    args = parser.parse_args()

    ran_any = False
    rc = 0

    if args.log is not None:
        ran_any = True
        rc |= extract_error_context(args.log, max(0, args.context))

    if args.validate is not None:
        ran_any = True
        rc |= validate_analysis(args.validate)

    if not ran_any:
        parser.print_help()
        return 1

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
