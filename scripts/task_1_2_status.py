#!/usr/bin/env python3
"""
Task 1.2 Status Report — Comprehensive Diagnostic
Checks vplan_mapping.yaml format, test decorators, docstrings, test function existence
"""

import yaml
import sys
import re
from pathlib import Path


def check_submission(submission_dir: Path) -> dict:
    """Return detailed status of a submission"""
    status = {
        "dut": submission_dir.name.replace("submission-1.2-", ""),
        "vplan_file_exists": False,
        "vplan_valid_yaml": False,
        "mappings_count": 0,
        "format_issues": [],
        "function_issues": [],
        "decorator_issues": [],
        "docstring_issues": [],
        "tests_dir_exists": False,
        "test_files_found": 0,
    }

    vplan_file = submission_dir / "vplan_mapping.yaml"
    if not vplan_file.exists():
        return status

    status["vplan_file_exists"] = True

    try:
        with open(vplan_file) as f:
            vplan = yaml.safe_load(f)
        status["vplan_valid_yaml"] = True
    except Exception as e:
        status["format_issues"].append(f"Invalid YAML: {e}")
        return status

    mappings = vplan.get("mappings", [])
    status["mappings_count"] = len(mappings)

    # Check vplan_mapping.yaml format
    for i, mapping in enumerate(mappings):
        vp_id = mapping.get("vp_id", "")
        test_name = mapping.get("test_name", "")

        # Check format
        if not test_name:
            status["format_issues"].append(f"Mapping {i}: missing test_name")
            continue

        # ❌ CRITICAL: Check for "tests." prefix (should NOT be there)
        if test_name.startswith("tests."):
            status["format_issues"].append(
                f"Mapping {i} ({vp_id}): test_name should NOT start with 'tests.'\n"
                f"  Found: {test_name}\n"
                f"  Fix to: {test_name.replace('tests.', '')}"
            )

        # Check separator
        if "::" not in test_name:
            status["format_issues"].append(
                f"Mapping {i}: test_name missing '::' separator"
            )

    # Check test files and function existence
    tests_dir = submission_dir / "tests"
    if tests_dir.exists():
        status["tests_dir_exists"] = True
        test_files = sorted(tests_dir.glob("test_vp_*.py"))
        status["test_files_found"] = len(test_files)

        for mapping in mappings:
            vp_id = mapping.get("vp_id", "")
            test_name = mapping.get("test_name", "")

            if not test_name or "::" not in test_name:
                continue

            # Parse test_name
            module_file, func_name = test_name.split("::")
            module_file_clean = module_file.replace(
                "tests.", ""
            )  # Remove prefix if present
            test_file = tests_dir / f"{module_file_clean}.py"

            if not test_file.exists():
                status["function_issues"].append(
                    f"{vp_id}: test file '{module_file_clean}.py' not found"
                )
                continue

            with open(test_file) as f:
                content = f.read()

            # Check @cocotb.test() decorator
            if "@cocotb.test()" not in content:
                status["decorator_issues"].append(
                    f"{vp_id}: missing @cocotb.test() decorator"
                )

            # Check docstring with VP-ID
            if vp_id not in content:
                status["docstring_issues"].append(
                    f"{vp_id}: VP-ID not found in docstring/comments"
                )

            # Check async function exists
            if f"async def {func_name}" not in content:
                status["function_issues"].append(
                    f"{vp_id}: function '{func_name}' not found"
                )

    return status


def main():
    """Check all submissions"""
    submissions_dir = Path("submissions/task-1.2")
    submissions = sorted(
        [
            d
            for d in submissions_dir.iterdir()
            if d.is_dir() and d.name.startswith("submission-1.2-")
        ]
    )

    print("=" * 100)
    print("TASK 1.2 STATUS REPORT")
    print("=" * 100)
    print()

    all_issues = []

    for subdir in submissions:
        status = check_submission(subdir)
        dut = status["dut"]

        print(f"📋 {dut.upper()}")
        print("-" * 100)

        # Summary
        print(
            f"  vplan_mapping.yaml: {'✓ Found' if status['vplan_file_exists'] else '✗ MISSING'}"
        )
        print(f"  YAML valid: {'✓ Yes' if status['vplan_valid_yaml'] else '✗ NO'}")
        print(f"  Total mappings: {status['mappings_count']}")
        print(
            f"  tests/ dir: {'✓ Found' if status['tests_dir_exists'] else '✗ MISSING'}"
        )
        print(f"  Test files: {status['test_files_found']}")

        # Issues
        if status["format_issues"]:
            print(f"\n  ❌ FORMAT ISSUES ({len(status['format_issues'])}):")
            for issue in status["format_issues"]:
                print(f"     {issue}")
                all_issues.append(("FORMAT", dut, issue))

        if status["function_issues"]:
            print(f"\n  ❌ FUNCTION ISSUES ({len(status['function_issues'])}):")
            for issue in status["function_issues"]:
                print(f"     {issue}")
                all_issues.append(("FUNCTION", dut, issue))

        if status["decorator_issues"]:
            print(f"\n  ❌ DECORATOR ISSUES ({len(status['decorator_issues'])}):")
            for issue in status["decorator_issues"]:
                print(f"     {issue}")
                all_issues.append(("DECORATOR", dut, issue))

        if status["docstring_issues"]:
            print(
                f"\n  ⚠️  DOCSTRING ISSUES ({len(status['docstring_issues'])} - Warning only):"
            )
            for issue in status["docstring_issues"][:3]:  # Show first 3
                print(f"     {issue}")
            if len(status["docstring_issues"]) > 3:
                print(f"     ... and {len(status['docstring_issues']) - 3} more")

        if not (
            status["format_issues"]
            or status["function_issues"]
            or status["decorator_issues"]
        ):
            print(f"\n  ✅ NO CRITICAL ISSUES FOUND")

        print()

    # Summary
    print("=" * 100)
    print("CRITICAL ISSUE SUMMARY")
    print("=" * 100)

    if not all_issues:
        print("✅ ALL SUBMISSIONS LOOK GOOD")
    else:
        format_issues = [i for i in all_issues if i[0] == "FORMAT"]
        function_issues = [i for i in all_issues if i[0] == "FUNCTION"]
        decorator_issues = [i for i in all_issues if i[0] == "DECORATOR"]

        if format_issues:
            print(f"\n❌ FORMAT ISSUES ({len(format_issues)}):")
            print("   These will CAUSE EVALUATION FAILURE\n")
            for cat, dut, issue in format_issues[:5]:
                print(f"   • {dut}: {issue[:80]}")

        if function_issues:
            print(f"\n❌ FUNCTION ISSUES ({len(function_issues)}):")
            print("   These will CAUSE TEST EXECUTION FAILURE\n")
            for cat, dut, issue in function_issues[:5]:
                print(f"   • {dut}: {issue}")

        if decorator_issues:
            print(f"\n❌ DECORATOR ISSUES ({len(decorator_issues)}):")
            print("   Tests won't be discovered by cocotb\n")
            for cat, dut, issue in decorator_issues[:5]:
                print(f"   • {dut}: {issue}")

    print("\n" + "=" * 100)
    return 0 if not all_issues else 1


if __name__ == "__main__":
    sys.exit(main())
