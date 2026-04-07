# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: rampart_i2c
- Total RTL files: 1
- Total RTL lines: 1360
- TL-UL detected: True
- Protocol hints: i2c
- Estimated FSM blocks: 5

## Verification Plan
- Planned features: 11
- Directed tests: 7
- Random tests: 4
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 1
- Random tests generated: 1
- Simulation run count: 4
- Simulation pass: True
- Selected top module: rampart_i2c

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 10.36%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 36.23%
- Code coverage source: verilator_lcov
- Functional coverage source: functional_bins_from_test_snapshots

## Bugs Found
- Static bug hypotheses: 0
- Detailed records are located in `bug_reports/`.

## Agent Methodology
- Iterations performed: 2
- LLM provider: openai
- LLM mode observed: online
- LLM calls: 14
- Estimated tokens: 18107

## Executive Summary
Verification was generated for the `rampart_i2c` module using a mix of 1 directed and 1 random test, with coverage focused on CSR access, reset behavior, host/target mode control, FIFO/status handling, interrupt semantics, timing register programming, and basic bus override/loopback operation. The environment validated TL-UL CSR read/write behavior with same-cycle response checking, reset-value correctness, open-drain SCL/SDA modeling with contention-aware sampling, and basic command sequencing in both host and target modes. It also exercised FIFO control/status paths, interrupt state/enable/test CSRs with W1C behavior, and smoke-level observation of arbitration-loss and timeout/error conditions, including simple concurrent host/target enable interactions. Functional coverage reached 36.23%, indicating meaningful feature sampling but not exhaustive closure. Remaining risk is concentrated in deeper protocol corner cases, multi-transaction concurrency, and error recovery behavior, since no bug hypotheses were generated and several checks were only smoke-level rather than fully stress-tested.
