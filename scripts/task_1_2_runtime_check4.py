#!/usr/bin/env python3
# pyright: reportMissingTypeStubs=false
"""Validate Task 1.2 runtime coverage-bin hits against vplan_mapping claims.

This checker enforces Check 4 using runtime artifacts produced during cocotb test
execution (TASK12_RUNTIME_COVERAGE_FILE JSON).
"""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import sys
from pathlib import Path
from typing import Any

yaml = importlib.import_module("yaml")


def flatten_bins(raw: Any) -> set[str]:
    """Flatten nested coverage_bins structures into canonical string bin names."""
    out: set[str] = set()

    def walk(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                out.add(str(key))
                walk(value)
            return
        if isinstance(node, (list, tuple, set)):
            for value in node:
                walk(value)
            return
        out.add(str(node))

    walk(raw)
    return out


def load_claimed_bins(mapping_path: Path) -> set[str]:
    data = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    mappings = data.get("mappings", []) if isinstance(data, dict) else []
    claimed: set[str] = set()
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        claimed.update(flatten_bins(mapping.get("coverage_bins", [])))
    return claimed


def mapping_keys(test_name: str) -> set[str]:
    """Generate equivalent key forms used by runtime instrumentation."""
    if "::" not in test_name:
        return set()
    module_name, func_name = test_name.split("::", 1)
    module_leaf = module_name.split(".")[-1]
    module_variants = {
        module_name,
        module_leaf,
        f"tests.{module_name}",
        f"tests.{module_leaf}",
    }
    return {f"{module}::{func_name}" for module in module_variants}


def count_asserts_in_test(test_file: Path, func_name: str) -> int:
    """Count explicit assert statements inside the mapped test function."""
    try:
        tree = ast.parse(test_file.read_text(encoding="utf-8"), filename=str(test_file))
    except Exception:
        return 0

    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == func_name
        ):
            return sum(1 for inner in ast.walk(node) if isinstance(inner, ast.Assert))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", required=True, help="Path to vplan_mapping.yaml")
    parser.add_argument(
        "--runtime-coverage",
        required=True,
        help="Path to runtime coverage JSON generated during simulation",
    )
    parser.add_argument("--dut", required=True, help="DUT name")
    parser.add_argument("--sim", required=True, help="Simulator name")
    parser.add_argument(
        "--max-missing-print",
        type=int,
        default=20,
        help="Maximum missing bins to print",
    )
    args = parser.parse_args()

    mapping_path = Path(args.mapping)
    runtime_path = Path(args.runtime_coverage)

    if not mapping_path.is_file():
        print(f"[FAIL] {args.dut}@{args.sim} — mapping file missing: {mapping_path}")
        return 1

    if not runtime_path.is_file():
        print(
            f"[FAIL] {args.dut}@{args.sim} — runtime coverage artifact missing: {runtime_path}"
        )
        return 1

    claimed_bins = load_claimed_bins(mapping_path)
    if not claimed_bins:
        print(
            f"[FAIL] {args.dut}@{args.sim} — no claimed coverage_bins found in {mapping_path.name}"
        )
        return 1

    payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    hit_bins = {str(x) for x in payload.get("hit_bins", [])}
    runtime_errors = payload.get("runtime_errors", [])
    passed_tests = {str(x) for x in payload.get("passed_tests", [])}
    seen_tests = {str(x) for x in payload.get("seen_tests", [])}

    missing_bins = sorted(claimed_bins - hit_bins)

    if runtime_errors:
        print(
            f"[FAIL] {args.dut}@{args.sim} — runtime coverage instrumentation errors:"
        )
        for item in runtime_errors:
            print(f"  - {item}")
        return 1

    if missing_bins:
        print(
            f"[FAIL] {args.dut}@{args.sim} — Check 4 failed: {len(missing_bins)} missing coverage bin(s)"
        )
        for item in missing_bins[: args.max_missing_print]:
            print(f"  - {item}")
        if len(missing_bins) > args.max_missing_print:
            extra = len(missing_bins) - args.max_missing_print
            print(f"  ... and {extra} more")
        return 1

    mapping_data = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    mappings = (
        mapping_data.get("mappings", []) if isinstance(mapping_data, dict) else []
    )

    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue

        vp_id = str(mapping.get("vp_id", ""))
        test_name = str(mapping.get("test_name", ""))
        if "::" not in test_name:
            print(f"[FAIL] {args.dut}@{args.sim} — {vp_id}: invalid test_name format")
            return 1

        module_name, func_name = test_name.split("::", 1)
        module_leaf = module_name.split(".")[-1]
        test_file = mapping_path.parent / "tests" / f"{module_leaf}.py"

        candidate_keys = mapping_keys(test_name)
        if not any(key in seen_tests for key in candidate_keys):
            print(
                f"[FAIL] {args.dut}@{args.sim} — {vp_id}: mapped test did not execute ({test_name})"
            )
            return 1

        if not any(key in passed_tests for key in candidate_keys):
            print(
                f"[FAIL] {args.dut}@{args.sim} — {vp_id}: mapped test did not pass ({test_name})"
            )
            return 1

        if not test_file.is_file():
            print(
                f"[FAIL] {args.dut}@{args.sim} — {vp_id}: mapped test file missing ({test_file})"
            )
            return 1

        assert_count = count_asserts_in_test(test_file, func_name)
        if assert_count < 1:
            print(
                f"[FAIL] {args.dut}@{args.sim} — {vp_id}: mapped test has no explicit assert checks"
            )
            return 1

    print(
        f"[OK] {args.dut}@{args.sim} — Check 4 passed: "
        f"claimed={len(claimed_bins)} hit={len(hit_bins)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
