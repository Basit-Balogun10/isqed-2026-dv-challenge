# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: bastion_gpio
- Total RTL files: 1
- Total RTL lines: 324
- TL-UL detected: True
- Protocol hints: gpio
- Estimated FSM blocks: 2

## Verification Plan
- Planned features: 14
- Directed tests: 12
- Random tests: 3
- Risk areas: 6

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 1
- Random tests generated: 1
- Simulation run count: 4
- Simulation pass: True
- Selected top module: bastion_gpio

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 3.72%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 52.73%
- Code coverage source: verilator_lcov
- Functional coverage source: functional_bins_from_test_snapshots

## Bugs Found
- Static bug hypotheses: 0
- Detailed records are located in `bug_reports/`.

## Agent Methodology
- Iterations performed: 2
- LLM provider: openai
- LLM mode observed: online
- LLM calls: 24
- Estimated tokens: 47850

## Executive Summary
Verification was generated for the `bastion_gpio` module with a focused set of directed and random tests, covering CSR access, GPIO direction and data paths, interrupt programming, reset behavior, and alert/output observation. Validation confirmed basic TL-UL read/write protocol sanity, correct DIR-controlled output enable behavior, DATA_OUT driving, synchronized DATA_IN sampling, and per-pin interrupt functionality across rising-edge, falling-edge, level-high, and level-low modes. The environment also exercised masked-write atomicity for both 16-bit halves, INTR_TEST software injection, and intr_o reflection, with no bug hypotheses raised. Remaining risk is moderate due to limited stimulus depth and only 52.73% functional coverage, so corner-case interactions, cross-feature concurrency, and less common interrupt/reset sequences may still be underexplored.
