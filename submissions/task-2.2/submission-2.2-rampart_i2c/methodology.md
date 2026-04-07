# Methodology

This document records the actual Task 2.2 execution history for
submission-2.2-rampart_i2c under Path A.

Task context:

-   Task: 2.2 (Stimulus Engineering)
-   DUT: rampart_i2c
-   Coverage-focused tests added:
    -   tests/test_coverage_timing_fifo.py
    -   tests/test_coverage_host_target_paths.py
-   Measured coverage delta from results files:
    -   line: 49.33 -> 56.57 (+7.24)
    -   branch: 23.49 -> 52.51 (+29.02)
    -   toggle: 25.0 -> 55.77 (+30.77)
    -   functional: 20.0 -> 100.0 (+80.0)

Master transcript source for prompt evidence:

-   Repository path: submissions/task-2.2/prompts.md
-   GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-2.2/prompts.md

## AI Tools Used

-   GitHub Copilot (GPT-5.3-Codex) for requirement-grounded test design, coverage collector integration, and readiness script hardening.
-   Local shell simulation loop for compile, smoke, and coverage measurement.
-   Existing Task 1.2 cocotb/TL-UL infrastructure reused as baseline.

## Prompt Engineering Strategies

-   Requirement-anchored prompting: converted Task 2.2 requirements into concrete file updates before coding.
-   Gap-driven prompting: targeted FIFO boundary behavior, host/target path coverage, and timing-sensitive branches.
-   Portability prompting: validated simulator-safe behavior under Icarus and Verilator during iteration.
-   Packaging prompting: included prompt evidence, methodology, and zip hygiene in every iteration gate.

## Iteration Process

1. Audited scoring and deliverable requirements from task and submission docs.
2. Preserved reference test flow and added two targeted coverage tests for uncovered control and FIFO paths.
3. Extended and validated functional coverage collection against these new paths.
4. Ran repeated compile/smoke loops on both simulators and coverage loops on Verilator.
5. Updated coverage_before and coverage_after with measured deltas.
6. Performed ZIP-first readiness verification and compliance cleanup before final packaging.

## Human vs AI Contribution

-   Human-led: strategy prioritization for Tier-4 value and final compliance decisions.
-   AI-led: implementation of coverage tests, automation checks, and artifact validation.
-   Joint: bug-risk triage and final submit/no-submit gates.

## Failed Approaches

-   Generic random stimulus yielded weaker branch closure than targeted path-specific tests.
-   Initial reliance on runtime checks alone did not catch all packaging policy risks.
-   Some constraints were too broad for efficient closure and were tightened to deterministic boundary stimuli.

## Efficiency Metrics

-   Coverage-focused tests in this DUT submission: 2.
-   Final coverage run summary for this DUT suite: TESTS=28 PASS=28 FAIL=0.
-   Final readiness result: dual-simulator smoke pass, structure pass, and ZIP generation pass.

## Reproducibility

Environment:

-   Path A (cocotb + open-source simulators)
-   Python virtual environment at .venv

Core commands:

1. source .venv/bin/activate
2. cd submissions/task-2.2/submission-2.2-rampart_i2c
3. make SIM=icarus compile DUT_PATH=../../../duts
4. make SIM=verilator compile DUT_PATH=../../../duts
5. make coverage SIM=verilator
6. cd ../../..
7. bash scripts/verify-2.2-readiness.sh --sim both --timeout 300
