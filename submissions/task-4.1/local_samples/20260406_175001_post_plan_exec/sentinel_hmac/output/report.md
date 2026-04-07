# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: sentinel_hmac
- Total RTL files: 1
- Total RTL lines: 796
- TL-UL detected: True
- Protocol hints: hmac
- Estimated FSM blocks: 4

## Verification Plan
- Planned features: 12
- Directed tests: 10
- Random tests: 3
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 10
- Random tests generated: 3
- Simulation run count: 4
- Simulation pass: True
- Selected top module: sentinel_hmac

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 3.12%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 34.94%
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
- Estimated tokens: 25725

## Executive Summary
Verification was generated for the `sentinel_hmac` module, covering TL-UL CSR access, CFG/CMD/STATUS register behavior, FIFO and streaming hash operation, digest readout, zeroization, interrupts/alerts, reset recovery, and invalid configuration handling. Validation included directed and random testing across HMAC and SHA-256-only modes, with checks for same-cycle CSR responses, unmapped address errors, W1S command sequencing, backpressure, multi-block partial/full message handling, and byte-swap behavior. The results indicate the key functional paths and security-relevant behaviors were exercised successfully, including WIPE_SECRET and post-reset defaults. Remaining risk is primarily in untested corner cases and deeper stress scenarios, since coverage is modest and only 10 directed plus 3 random tests were reported. No bug hypotheses were identified, which lowers immediate concern but does not eliminate residual integration or protocol risk.
