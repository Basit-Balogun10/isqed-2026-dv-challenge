# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: aegis_aes
- Total RTL files: 1
- Total RTL lines: 706
- TL-UL detected: True
- Protocol hints: aes
- Estimated FSM blocks: 8

## Verification Plan
- Planned features: 15
- Directed tests: 8
- Random tests: 4
- Risk areas: 8

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 8
- Random tests generated: 4
- Simulation run count: 4
- Simulation pass: True
- Selected top module: aegis_aes

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 3.3%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 38.67%
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
- Estimated tokens: 20612

## Executive Summary
Verification was generated for the `aegis_aes` module, covering TL-UL CSR access, AES-128 ECB/CBC encrypt/decrypt flows, 128-bit key/data programming, start/interrupt sequencing, status polling, back-to-back block operation, clear/reset behavior, basic protocol compliance, alert observation, and FSM progression through IDLE, KEY_EXPAND, INIT_CBC, ROUND, and DONE. The environment included 8 directed and 4 random tests, achieving 38.67% functional coverage. Validation confirmed the core register interface and functional control paths, along with expected data movement and state transitions for legal transactions. Remaining risk is moderate to high due to limited coverage depth, especially around corner cases, error recovery, and broader protocol stress since no bug hypotheses were generated and coverage is still below full closure.
