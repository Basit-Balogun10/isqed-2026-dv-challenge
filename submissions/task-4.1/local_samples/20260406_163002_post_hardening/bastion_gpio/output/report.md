# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: bastion_gpio
- Total RTL files: 1
- Total RTL lines: 324
- TL-UL detected: True
- Protocol hints: gpio
- Estimated FSM blocks: 2

## Verification Plan
- Planned features: 15
- Directed tests: 18
- Random tests: 7
- Risk areas: 10

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
- Functional coverage: 45.45%
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
- Estimated tokens: 38100

## Executive Summary
Verification generated one directed and one random test for the `bastion_gpio` module, with 45.45% functional coverage and no bug hypotheses raised. The environment validated TL-UL CSR access, reset behavior, per-pin direction control, DATA_OUT/DATA_IN behavior, input synchronization latency, interrupt generation and masking, INTR_TEST injection, masked-write atomicity, multi-pin activity, and basic invalid-access robustness. It also confirmed expected readback semantics for the masked-write CSRs and quiescent alert behavior during legal operation. The main remaining risk is coverage depth: the stimulus set is small, so corner cases around timing, simultaneous edge/level interrupt interactions, and broader protocol error handling may still be under-exercised.
