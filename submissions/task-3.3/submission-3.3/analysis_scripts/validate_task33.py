#!/usr/bin/env python3
"""Structural validator for Task 3.3 submission artifacts."""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections import Counter
from typing import Any

import yaml  # type: ignore[import-untyped]


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


def load_yaml(path: pathlib.Path) -> Any:
    if not path.exists():
        fail(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(submission_dir: pathlib.Path, failure_details_path: pathlib.Path, patches_dir: pathlib.Path) -> None:
    required_files = [
        submission_dir / "bucketing.yaml",
        submission_dir / "bug_descriptions.yaml",
        submission_dir / "priority_ranking.yaml",
        submission_dir / "patch_validation.yaml",
        submission_dir / "metadata.yaml",
        submission_dir / "methodology.md",
        submission_dir / "Makefile",
    ]
    for path in required_files:
        if not path.exists():
            fail(f"Missing required file: {path}")

    failure_data = load_yaml(failure_details_path)
    expected_failure_ids = {entry["test_id"] for entry in failure_data["failures"]}

    bucketing = load_yaml(submission_dir / "bucketing.yaml")
    buckets = bucketing.get("buckets")
    if not isinstance(buckets, list) or not buckets:
        fail("bucketing.yaml must define non-empty 'buckets' list")

    bucket_ids = []
    assigned_failure_ids: list[str] = []
    for bucket in buckets:
        if "bucket_id" not in bucket:
            fail("Each bucket requires 'bucket_id'")
        if "failure_ids" not in bucket:
            fail(f"Bucket {bucket.get('bucket_id')} missing 'failure_ids'")
        ids = bucket["failure_ids"]
        if not isinstance(ids, list) or not ids:
            fail(f"Bucket {bucket['bucket_id']} failure_ids must be non-empty list")
        bucket_ids.append(bucket["bucket_id"])
        assigned_failure_ids.extend(ids)

    assigned_counter = Counter(assigned_failure_ids)
    duplicates = [k for k, v in assigned_counter.items() if v > 1]
    if duplicates:
        fail(f"Duplicate failure IDs across buckets: {sorted(duplicates)}")

    assigned_set = set(assigned_failure_ids)
    missing = sorted(expected_failure_ids - assigned_set)
    extras = sorted(assigned_set - expected_failure_ids)
    if missing:
        fail(f"Unassigned failure IDs: {missing}")
    if extras:
        fail(f"Unknown failure IDs in buckets: {extras}")

    bug_desc = load_yaml(submission_dir / "bug_descriptions.yaml")
    bugs = bug_desc.get("bugs")
    if not isinstance(bugs, list) or not bugs:
        fail("bug_descriptions.yaml must define non-empty 'bugs' list")
    desc_bucket_ids = {b.get("bucket_id") for b in bugs}
    if desc_bucket_ids != set(bucket_ids):
        fail(
            "bug_descriptions.yaml bucket coverage mismatch with bucketing.yaml "
            f"(have {sorted(desc_bucket_ids)}, expected {sorted(set(bucket_ids))})"
        )

    priority = load_yaml(submission_dir / "priority_ranking.yaml")
    ranking = priority.get("ranking")
    if not isinstance(ranking, list) or not ranking:
        fail("priority_ranking.yaml must define non-empty 'ranking' list")

    seen_ranks = []
    rank_bucket_ids = []
    for item in ranking:
        if not all(k in item for k in ("rank", "bucket_id", "severity", "rationale")):
            fail("Each ranking entry must include rank, bucket_id, severity, rationale")
        seen_ranks.append(item["rank"])
        rank_bucket_ids.append(item["bucket_id"])

    expected_ranks = list(range(1, len(ranking) + 1))
    if sorted(seen_ranks) != expected_ranks:
        fail(f"priority ranks must be contiguous {expected_ranks}, got {sorted(seen_ranks)}")
    if set(rank_bucket_ids) != set(bucket_ids):
        fail("priority_ranking.yaml must rank every bucket exactly once")

    patch_validation = load_yaml(submission_dir / "patch_validation.yaml")
    validations = patch_validation.get("validations")
    if not isinstance(validations, list) or not validations:
        fail("patch_validation.yaml must define non-empty 'validations' list")

    expected_patch_files = sorted(p.name for p in patches_dir.glob("patch_*.diff"))
    if not expected_patch_files:
        fail(f"No patch files found under {patches_dir}")

    seen_patch_ids = set()
    for item in validations:
        for key in ("patch_id", "fixes_bucket", "introduces_regression", "regression_details"):
            if key not in item:
                fail(f"patch_validation entry missing key '{key}'")
        if item["fixes_bucket"] not in set(bucket_ids):
            fail(f"Unknown fixes_bucket {item['fixes_bucket']} in patch_validation")
        if not isinstance(item["introduces_regression"], bool):
            fail("introduces_regression must be boolean")
        seen_patch_ids.add(item["patch_id"])

    if len(validations) != len(expected_patch_files):
        fail(
            f"Expected {len(expected_patch_files)} patch validation entries "
            f"(from patches dir), found {len(validations)}"
        )

    print("[OK] Task 3.3 structural validation passed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Task 3.3 submission artifacts")
    parser.add_argument("--submission-dir", required=True, help="Path to submission-3.3 directory")
    parser.add_argument(
        "--failure-details",
        default="phase3_materials/task_3_3_regression/failure_details.yaml",
        help="Path to failure_details.yaml",
    )
    parser.add_argument(
        "--patches-dir",
        default="phase3_materials/task_3_3_regression/patches",
        help="Path to directory containing patch_*.diff files",
    )
    args = parser.parse_args()

    submission_dir = pathlib.Path(args.submission_dir)
    failure_details_path = pathlib.Path(args.failure_details)
    patches_dir = pathlib.Path(args.patches_dir)

    validate(submission_dir, failure_details_path, patches_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
