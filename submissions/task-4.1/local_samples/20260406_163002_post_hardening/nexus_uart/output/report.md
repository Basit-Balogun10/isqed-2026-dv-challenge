# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: nexus_uart
- Total RTL files: 1
- Total RTL lines: 706
- TL-UL detected: True
- Protocol hints: uart
- Estimated FSM blocks: 4

## Verification Plan
- Planned features: 13
- Directed tests: 8
- Random tests: 3
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 1
- Random tests generated: 1
- Simulation run count: 4
- Simulation pass: True
- Selected top module: nexus_uart

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 5.22%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 53.19%
- Code coverage source: verilator_lcov
- Functional coverage source: functional_bins_from_test_snapshots

## Bugs Found
- Static bug hypotheses: 0
- Detailed records are located in `bug_reports/`.

## Agent Methodology
- Iterations performed: 2
- LLM provider: openai
- LLM mode observed: online
- LLM calls: 16
- Estimated tokens: 22414

## Executive Summary
Verification was generated for the `nexus_uart` module using 1 directed and 1 random test, achieving 53.19% functional coverage with no bug hypotheses raised. The environment validated TL-UL CSR access with single-cycle response checking, register programming for UART control fields, STATUS readback, TX/RX data paths, FIFO control and reset behavior, interrupt set/clear behavior, loopback operation, parity/stop-bit configuration, reset defaults, and unmapped address error responses. It also exercised FIFO overflow/underflow and sticky error behavior, along with basic timing sanity across a small set of baud divisors. The main remaining risk is incomplete coverage depth: the stimulus set is small, so corner-case interactions across baud rates, FIFO thresholds, interrupt races, and error recovery may still be underexplored.
