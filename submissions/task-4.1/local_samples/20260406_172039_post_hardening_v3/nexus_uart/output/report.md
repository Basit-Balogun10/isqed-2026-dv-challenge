# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: nexus_uart
- Total RTL files: 1
- Total RTL lines: 706
- TL-UL detected: True
- Protocol hints: uart
- Estimated FSM blocks: 4

## Verification Plan
- Planned features: 15
- Directed tests: 12
- Random tests: 4
- Risk areas: 6

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
- Functional coverage: 61.7%
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
- Estimated tokens: 26860

## Executive Summary
Verification was generated for the `nexus_uart` module, covering directed and random stimulus across CSR access, TX/RX datapaths, FIFO behavior, control/status programming, interrupt handling, loopback, and error conditions. Validation confirmed TL-UL single-cycle CSR responses, correct TXDATA/RXDATA paths, FIFO watermark and reset behavior, W1C interrupt handling, reset values, reserved-field RAZ/WI behavior, and unmapped address error responses. Functional coverage reached 61.7%, with exercised scenarios including parity/stop-bit configurations and characterization of RX overrun, parity, and frame errors. No bug hypotheses were identified, but residual risk remains due to incomplete coverage, especially around corner-case FIFO/interrupt interactions and less frequently used configuration combinations.
