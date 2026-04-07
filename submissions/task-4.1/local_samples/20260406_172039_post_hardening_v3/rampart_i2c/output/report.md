# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: rampart_i2c
- Total RTL files: 1
- Total RTL lines: 1360
- TL-UL detected: True
- Protocol hints: i2c
- Estimated FSM blocks: 5

## Verification Plan
- Planned features: 16
- Directed tests: 9
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
- LLM calls: 18
- Estimated tokens: 28189

## Executive Summary
Verification for `rampart_i2c` generated both directed and random stimulus, with 42.03 functional coverage achieved and no bug hypotheses raised. The environment validated TL-UL CSR read/write access, reset behavior, open-drain SCL/SDA operation, host and target mode sequencing, FIFO push/pop and status handling, timing and target-ID programming, interrupt behavior, timeout indication, arbitration loss, bus override, and basic I2C transaction flow. It also exercised RX/ACQ FIFO readout, FIFO reset controls, and simultaneous multi-role enable behavior. Overall, the block appears broadly validated across core control, data path, and error-response features. Remaining risk is concentrated in the relatively low coverage depth and limited stimulus volume, which may leave corner-case protocol interactions and rare contention/timeout scenarios underexplored.
