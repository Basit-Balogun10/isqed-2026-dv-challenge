# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: warden_timer
- Total RTL files: 1
- Total RTL lines: 636
- TL-UL detected: True
- Protocol hints: timer
- Estimated FSM blocks: 1

## Verification Plan
- Planned features: 18
- Directed tests: 10
- Random tests: 4
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 1
- Random tests generated: 1
- Simulation run count: 4
- Simulation pass: True
- Selected top module: warden_timer

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 4.81%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 40.98%
- Code coverage source: verilator_lcov
- Functional coverage source: functional_bins_from_test_snapshots

## Bugs Found
- Static bug hypotheses: 0
- Detailed records are located in `bug_reports/`.

## Agent Methodology
- Iterations performed: 2
- LLM provider: openai
- LLM mode observed: online
- LLM calls: 20
- Estimated tokens: 34395

## Executive Summary
Verification for the `warden_timer` module generated a focused set of directed and random tests covering the 15-register TL-UL CSR map, 64-bit mtime/prescaler operation, both timer comparators, watchdog functionality, interrupt/alert paths, and access-policy enforcement. Validation confirmed reset behavior, prescaler programming and boundary cases, comparator partial-write semantics, INTR_STATE W1C, INTR_ENABLE masking, INTR_TEST forcing, watchdog pet/lock behavior, and reserved-bit/read-only/write-only handling. Concurrent timer and watchdog activity under bus traffic was also exercised to increase confidence in integration behavior. No bug hypotheses were identified, and functional coverage reached 40.98%, indicating the main remaining risk is incomplete coverage rather than known functional failures.
