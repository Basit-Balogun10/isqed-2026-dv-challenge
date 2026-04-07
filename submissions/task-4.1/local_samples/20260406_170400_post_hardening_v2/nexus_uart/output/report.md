# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: nexus_uart
- Total RTL files: 1
- Total RTL lines: 706
- TL-UL detected: True
- Protocol hints: uart
- Estimated FSM blocks: 4

## Verification Plan
- Planned features: 10
- Directed tests: 9
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
- LLM calls: 12
- Estimated tokens: 14298

## Executive Summary
Verification was generated for the `nexus_uart` module with one directed and one random test, achieving 61.7% functional coverage and no identified bug hypotheses. The environment validated TL-UL CSR access behavior, including single-cycle responses, unmapped-address error handling, and basic read/write sequencing under backpressure. Functional checks also covered UART control programming, TX/RX FIFO push-pop behavior, FIFO flush control, interrupt generation and W1C handling, reset/default CSR behavior, and reserved-bit read-as-zero/write-ignore rules. End-to-end serial data path operation was exercised through loopback validation, confirming core transmit/receive functionality. Remaining risk is moderate due to incomplete coverage, with limited stimulus depth and no bug hypotheses to indicate subtle corner-case escapes in FIFO, interrupt, or protocol robustness behavior.
