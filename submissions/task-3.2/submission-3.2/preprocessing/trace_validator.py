#!/usr/bin/env python3
"""Validation helper for Task 3.2 trace analysis YAML files."""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any

import yaml

REQUIRED_KEYS = {
    "failure_id",
    "manifestation_cycle",
    "root_cause_cycle",
    "root_cause_file",
    "root_cause_line",
    "signal_trace",
    "root_cause_description",
}


def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


def _validate_trace_item(item: dict[str, Any], file_name: str, idx: int) -> None:
    needed = {"cycle", "signal", "value", "note"}
    missing = needed.difference(item.keys())
    if missing:
        _fail(f"{file_name}: signal_trace[{idx}] missing keys: {sorted(missing)}")

    if not isinstance(item["cycle"], int):
        _fail(f"{file_name}: signal_trace[{idx}].cycle must be int")
    if item["cycle"] < 0:
        _fail(f"{file_name}: signal_trace[{idx}].cycle must be >= 0")

    for key in ("signal", "value", "note"):
        if not isinstance(item[key], str) or not item[key].strip():
            _fail(f"{file_name}: signal_trace[{idx}].{key} must be non-empty string")


def validate_analysis_dir(analysis_dir: pathlib.Path) -> None:
    expected = [analysis_dir / f"trace_{idx:02d}.yaml" for idx in range(1, 6)]
    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        _fail(f"Missing expected analysis files: {missing}")

    for expected_failure_id, path in enumerate(expected, start=1):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)

        if not isinstance(data, dict):
            _fail(f"{path.name}: top-level YAML must be a mapping")

        missing_keys = REQUIRED_KEYS.difference(data.keys())
        if missing_keys:
            _fail(f"{path.name}: missing required keys: {sorted(missing_keys)}")

        if data["failure_id"] != expected_failure_id:
            _fail(
                f"{path.name}: failure_id must be {expected_failure_id}, "
                f"got {data['failure_id']}"
            )

        for key in ("manifestation_cycle", "root_cause_cycle", "root_cause_line"):
            if not isinstance(data[key], int):
                _fail(f"{path.name}: {key} must be int")
            if data[key] < 0:
                _fail(f"{path.name}: {key} must be >= 0")

        if (
            not isinstance(data["root_cause_file"], str)
            or not data["root_cause_file"].strip()
        ):
            _fail(f"{path.name}: root_cause_file must be non-empty string")

        if (
            not isinstance(data["root_cause_description"], str)
            or not data["root_cause_description"].strip()
        ):
            _fail(f"{path.name}: root_cause_description must be non-empty string")

        trace = data["signal_trace"]
        if not isinstance(trace, list) or not trace:
            _fail(f"{path.name}: signal_trace must be a non-empty list")

        for idx, item in enumerate(trace):
            if not isinstance(item, dict):
                _fail(f"{path.name}: signal_trace[{idx}] must be a mapping")
            _validate_trace_item(item, path.name, idx)

    print("[OK] Task 3.2 analysis YAML validation passed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Task 3.2 trace YAML files")
    parser.add_argument("--validate", required=True, help="Path to analysis directory")
    args = parser.parse_args()

    analysis_dir = pathlib.Path(args.validate)
    if not analysis_dir.exists() or not analysis_dir.is_dir():
        _fail(f"Analysis directory does not exist: {analysis_dir}")

    validate_analysis_dir(analysis_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
