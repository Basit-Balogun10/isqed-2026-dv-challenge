# Methodology

This document records the actual Task 2.2 execution history for
submission-2.2-warden_timer under Path A.

Task context:
- Task: 2.2 (Stimulus Engineering)
- DUT: warden_timer
- Coverage-focused tests added:
	- tests/test_coverage_compare_interrupts.py
	- tests/test_coverage_watchdog_lock.py
- Measured coverage delta from results files:
	- line: 71.28 -> 97.50 (+26.22)
	- branch: 20.66 -> 79.03 (+58.37)
	- toggle: 25.0 -> 85.92 (+60.92)
	- functional: 20.0 -> 100.0 (+80.0)

Master transcript source for prompt evidence:
- Repository path: submissions/task-2.2/prompts.md
- GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-2.2/prompts.md

## AI Tools Used

- GitHub Copilot (GPT-5.3-Codex) for targeted timer/interrupt coverage test generation and script-level validation checks.
- Local shell simulation loop for compile, smoke, and coverage verification.
- Existing baseline cocotb harness reused where appropriate for faster iteration.

## Prompt Engineering Strategies

- Control-path-first prompting: targeted compare and watchdog lock/interrupt interactions that gate branch closure.
- Requirement-safe prompting: enforced Task 2.2 naming, results, and packaging constraints while generating tests.
- Iteration-safe prompting: kept tests deterministic and bounded to maintain fast coverage loops under time limits.
- Evidence-safe prompting: synchronized prompt artifacts to a single master transcript with chunked submission copies.

## Iteration Process

1. Audited Task 2.2 required outputs and scoring levers.
2. Preserved reference test and added two focused coverage tests for compare and watchdog lock behavior.
3. Confirmed functional coverage movement using repeated local coverage runs.
4. Verified dual-simulator compile/smoke readiness and corrected portability issues early.
5. Captured coverage_before and coverage_after metrics from final validated runs.
6. Performed ZIP-first readiness validation and compliance checks before signoff.

## Human vs AI Contribution

- Human-led: test intent prioritization and final quality/compliance decisions.
- AI-led: test implementation, coverage instrumentation updates, and verification automation checks.
- Joint: final regression triage and submission hardening.

## Failed Approaches

- Generic randomization did not reliably hit lock and interrupt edge interactions.
- Early broad test loops added runtime without proportional branch gain.
- Relying only on compile/smoke pass was insufficient without explicit packaging audits.

## Efficiency Metrics

- Coverage-focused tests in this DUT submission: 2.
- Final coverage run summary for this DUT suite: TESTS=3 PASS=3 FAIL=0.
- Final readiness result: dual-simulator smoke pass, structure pass, and ZIP generation pass.

## Reproducibility

Environment:
- Path A (cocotb + open-source simulators)
- Python virtual environment at .venv

Core commands:
1. source .venv/bin/activate
2. cd submissions/task-2.2/submission-2.2-warden_timer
3. make SIM=icarus compile DUT_PATH=../../../duts
4. make SIM=verilator compile DUT_PATH=../../../duts
5. make coverage SIM=verilator
6. cd ../../..
7. bash scripts/verify-2.2-readiness.sh --sim both --timeout 300
