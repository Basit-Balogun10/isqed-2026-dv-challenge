# Methodology

This document records the actual Task 2.2 execution history for
submission-2.2-aegis_aes under Path A.

Task context:

-   Task: 2.2 (Stimulus Engineering)
-   DUT: aegis_aes
-   Coverage-focused test added: tests/test_coverage_mode_sweep.py
-   Measured coverage delta from results files:
    -   line: 34.33 -> 54.93 (+20.60)
    -   branch: 8.11 -> 95.12 (+87.01)
    -   toggle: 25.0 -> 87.72 (+62.72)
    -   functional: 20.0 -> 100.0 (+80.0)

Master transcript source for prompt evidence:

-   Repository path: submissions/task-2.2/prompts.md
-   GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-2.2/prompts.md

## AI Tools Used

-   GitHub Copilot (GPT-5.3-Codex) for requirement-driven test generation, coverage collector extension, and readiness automation.
-   Local shell simulation loop for compile, smoke, and coverage verification.
-   Existing Task 1.2 cocotb/TL-UL infrastructure reused as baseline.

## Prompt Engineering Strategies

-   Requirement-anchored prompting: translated Task 2.2 required artifacts into concrete file-level updates first.
-   Gap-to-stimulus prompting: generated tests from uncovered control paths, then constrained them for deterministic coverage movement.
-   Compatibility prompting: enforced dual-simulator discipline (Icarus + Verilator smoke) while using Verilator for coverage extraction.
-   Packaging prompting: treated prompt evidence and ZIP content as first-class deliverables, not post-processing.

## Iteration Process

1. Performed a doc-level audit of Task 2.2, rubric, and submission format requirements.
2. Kept reference tests intact and added coverage-closing tests with the test*coverage* prefix.
3. Extended functional coverage collection to capture missing operational combinations.
4. Ran iterative compile/sim loops on both simulators to remove portability regressions early.
5. Executed coverage runs, updated coverage_before and coverage_after, and validated measurable improvements.
6. Ran ZIP-first readiness verification and final section-by-section compliance audit.

## Human vs AI Contribution

-   Human-led: scoring strategy decisions, submission prioritization, and final acceptance gates.
-   AI-led: implementation of coverage-closing tests, coverage collectors, script checks, and packaging updates.
-   Joint: regression triage and final compliance decisions for submission hygiene.

## Failed Approaches

-   Broad random-only stimulus had low branch closure efficiency compared with directed corner stimuli.
-   Some early checks focused only on runtime and missed packaging-policy risks, so explicit artifact scans were added.
-   Treating readiness pass as sufficient without payload inspection initially left avoidable compliance exposure.

## Efficiency Metrics

-   Coverage-focused tests in this DUT submission: 1.
-   Final coverage run summary for this DUT suite: TESTS=22 PASS=22 FAIL=0.
-   Final readiness result: dual-simulator smoke pass, structure pass, and ZIP generation pass.

## Reproducibility

Environment:

-   Path A (cocotb + open-source simulators)
-   Python virtual environment at .venv

Core commands:

1. source .venv/bin/activate
2. cd submissions/task-2.2/submission-2.2-aegis_aes
3. make SIM=icarus compile DUT_PATH=../../../duts
4. make SIM=verilator compile DUT_PATH=../../../duts
5. make coverage SIM=verilator
6. cd ../../..
7. bash scripts/verify-2.2-readiness.sh --sim both --timeout 300
