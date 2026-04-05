# Methodology

This document records the actual Task 2.2 execution history for
submission-2.2-sentinel_hmac under Path A.

Task context:
- Task: 2.2 (Stimulus Engineering)
- DUT: sentinel_hmac
- Coverage-focused test added: tests/test_coverage_intr_and_fifo.py
- Measured coverage delta from results files:
	- line: 47.49 -> 76.61 (+29.12)
	- branch: 6.58 -> 93.57 (+86.99)
	- toggle: 25.0 -> 87.01 (+62.01)
	- functional: 20.0 -> 100.0 (+80.0)

Master transcript source for prompt evidence:
- Repository path: submissions/task-2.2/prompts.md
- GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-2.2/prompts.md

## AI Tools Used

- GitHub Copilot (GPT-5.3-Codex) for scenario derivation, cocotb test implementation, and readiness validation automation.
- Local shell simulation loop for compile, smoke, and coverage runs.
- Existing Task 1.2 verification environment reused as the baseline scaffold.

## Prompt Engineering Strategies

- Gap-oriented prompting: focused on interrupt handling paths, FIFO status boundaries, and control-path branches.
- Deterministic closure prompting: prioritized bounded directed checks before broad randomized sweeps.
- Compliance prompting: kept submission-format requirements and dual-simulator checks in the prompt loop.
- Evidence prompting: maintained prompt-history traceability via a master transcript and chunked prompt files.

## Iteration Process

1. Completed requirement and rubric audit for Task 2.2 deliverables.
2. Preserved reference tests and added one dedicated coverage-closing test for interrupt and FIFO paths.
3. Updated functional coverage collection and validated bin hits with regression reruns.
4. Repeated dual-simulator compile/smoke loops and Verilator coverage loops.
5. Captured before/after coverage metrics and verified meaningful improvements.
6. Ran ZIP-first readiness checks and final artifact policy audit.

## Human vs AI Contribution

- Human-led: acceptance criteria, DUT prioritization, and final signoff decisions.
- AI-led: test coding, coverage model updates, script-level checks, and compliance validation.
- Joint: debugging decisions for coverage closure and packaging correctness.

## Failed Approaches

- Pure random stimulus did not efficiently close branch-heavy control logic.
- Overly broad initial test intent reduced iteration speed and observability.
- Runtime-only confidence was insufficient; explicit payload scans were required for final compliance.

## Efficiency Metrics

- Coverage-focused tests in this DUT submission: 1.
- Final coverage run summary for this DUT suite: TESTS=22 PASS=22 FAIL=0.
- Final readiness result: dual-simulator smoke pass, structure pass, and ZIP generation pass.

## Reproducibility

Environment:
- Path A (cocotb + open-source simulators)
- Python virtual environment at .venv

Core commands:
1. source .venv/bin/activate
2. cd submissions/task-2.2/submission-2.2-sentinel_hmac
3. make SIM=icarus compile DUT_PATH=../../../duts
4. make SIM=verilator compile DUT_PATH=../../../duts
5. make coverage SIM=verilator
6. cd ../../..
7. bash scripts/verify-2.2-readiness.sh --sim both --timeout 300
