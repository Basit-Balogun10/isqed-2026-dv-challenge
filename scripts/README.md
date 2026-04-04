# Scripts Guide

This directory contains the maintained automation scripts for submission packaging and validation.

## Task 1.1 Scripts

-   `manage-1.1-submissions.sh`

    -   Package, extract, verify, and report status for Task 1.1 submission folders.
    -   Typical usage:
        -   `bash scripts/manage-1.1-submissions.sh status`
        -   `bash scripts/manage-1.1-submissions.sh verify`
        -   `bash scripts/manage-1.1-submissions.sh rebuild-all`

-   `test-1.1-submissions.sh`

    -   Reverse-test Task 1.1 submission ZIPs with Icarus and/or Verilator.
    -   Typical usage:
        -   `source .venv/bin/activate`
        -   `bash scripts/test-1.1-submissions.sh -s both`

-   `verify-1.1-readiness.sh`
    -   ZIP-first Task 1.1 readiness verification.
    -   Rebuilds ZIPs, extracts and validates required files from extracted content, then reverse-tests ZIPs.
    -   Typical usage:
        -   `source .venv/bin/activate`
        -   `bash scripts/verify-1.1-readiness.sh --sim both`

## Task 1.2 Scripts

-   `manage-1.2-submissions.sh`

    -   Package, extract, verify, and report status for Task 1.2 submission folders.
    -   Typical usage:
        -   `bash scripts/manage-1.2-submissions.sh status`
        -   `bash scripts/manage-1.2-submissions.sh package-all`
        -   `bash scripts/manage-1.2-submissions.sh verify`

-   `test-1.2-submissions.sh`

    -   Runs Task 1.2 evaluation-style checks: 1. `vplan_mapping.yaml` parse + structure 2. mapped cocotb test function existence 3. clean RTL simulation pass/fail on selected simulators 4. runtime Check 4 coverage-bin validation from executed tests
    -   Typical usage:
        -   `source .venv/bin/activate`
        -   `bash scripts/test-1.2-submissions.sh -s both`

-   `task_1_2_runtime_check4.py`

    -   Helper utility used by Task 1.2 scripts to validate claimed `coverage_bins` against runtime coverage artifacts.

-   `verify-1.2-readiness.sh`
    -   ZIP-first Task 1.2 readiness verification.
    -   Packages ZIPs, validates extracted ZIP content and mapping/test consistency, then reverse-tests extracted ZIPs.
    -   Enforces Check 4 using runtime coverage artifacts from each DUT/simulator run.
    -   Typical usage:
        -   `source .venv/bin/activate`
        -   `bash scripts/verify-1.2-readiness.sh --sim both`

## Unified Workflow

-   `verify-readiness.sh`

    -   Generic task-driven readiness runner.
    -   Runs one or more per-task readiness scripts in sequence.
    -   Typical usage:
        -   `source .venv/bin/activate`
        -   `bash scripts/verify-readiness.sh --tasks 1.1,1.2 --sim both`
        -   `bash scripts/verify-readiness.sh 1.2 --sim icarus --quick`

-   `docs/VERIFY_1_1_1_2_WORKFLOW.md`
    -   Manual command checklist version of the same flow.
