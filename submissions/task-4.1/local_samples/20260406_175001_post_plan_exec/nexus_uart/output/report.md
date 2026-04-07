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
- Directed tests: 8
- Random tests: 5
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 8
- Random tests generated: 5
- Simulation run count: 4
- Simulation pass: True
- Selected top module: nexus_uart

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 5.51%
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
- LLM calls: 14
- Estimated tokens: 18108

## Executive Summary
Verification was generated for the `nexus_uart` module, covering TL-UL CSR access, full-duplex TX/RX datapaths, 32-byte FIFOs, programmable framing/loopback controls, status and interrupt behavior, reset/reserved-bit handling, unmapped address errors, and basic fatal alert observation. The testbench executed 8 directed and 5 random tests, achieving 61.7% functional coverage. Validation confirmed the core register interface behavior, FIFO and datapath operation, interrupt state/enable/clear sequencing, and key error/response paths. No bug hypotheses were identified during this run. The main residual risk is incomplete coverage, especially around corner-case UART timing, FIFO boundary conditions, and less common error/alert scenarios that may not be fully exercised by the current stimulus.
