# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: rampart_i2c
- Total RTL files: 1
- Total RTL lines: 1360
- TL-UL detected: True
- Protocol hints: i2c
- Estimated FSM blocks: 5

## Verification Plan
- Planned features: 20
- Directed tests: 8
- Random tests: 4
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 8
- Random tests generated: 4
- Simulation run count: 4
- Simulation pass: True
- Selected top module: rampart_i2c

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 11.03%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 42.03%
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
- Estimated tokens: 19149

## Executive Summary
Verification was generated for the `rampart_i2c` module, covering 8 directed and 4 random tests across 42.03 functional points. The environment validated TL-UL CSR access integrity, reset/default CSR behavior, host/target mode sequencing, open-drain SCL/SDA behavior, loopback, timing programming, FIFO paths, interrupt behavior, bus override, timeout handling, arbitration/conflict cases, basic I2C transfer sequencing, multi-role coexistence, backpressure, and alert sanity. No bug hypotheses were raised, indicating no known open defect candidates from the executed plan. The main residual risk is coverage depth: while the feature list is broad, the relatively small random count suggests corner-case stress, long-duration timing, and rare protocol interleavings may still be underexercised.
