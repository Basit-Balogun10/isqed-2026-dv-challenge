# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: rampart_i2c
- Total RTL files: 1
- Total RTL lines: 1360
- TL-UL detected: True
- Protocol hints: i2c
- Estimated FSM blocks: 5

## Verification Plan
- Planned features: 19
- Directed tests: 12
- Random tests: 5
- Risk areas: 8

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
- LLM calls: 12
- Estimated tokens: 14726

## Executive Summary
Verification for `rampart_i2c` generated a focused testbench and stimulus set covering the 19-register TL-UL CSR map, reset/default behavior, FIFO datapaths, timing/timeout programming, interrupt controls, open-drain behavior, and both host/target I2C sequencing. Validation included directed and random testing, with functional coverage reaching 42.03%, indicating meaningful exercise of the implemented register and protocol features. The environment also checked arbitration loss, bus override/debug behavior, and concurrent host/target enable interactions to confirm priority and mode-control handling. No bug hypotheses were raised, suggesting no known functional failures from the executed scenarios. Remaining risk is primarily coverage-related: 42% functional coverage leaves unexercised corner cases, especially around deeper protocol timing, rare error paths, and broader multi-master/target interaction scenarios.
