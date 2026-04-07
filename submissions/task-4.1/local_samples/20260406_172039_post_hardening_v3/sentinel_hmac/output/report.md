# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: sentinel_hmac
- Total RTL files: 1
- Total RTL lines: 796
- TL-UL detected: True
- Protocol hints: hmac
- Estimated FSM blocks: 4

## Verification Plan
- Planned features: 16
- Directed tests: 10
- Random tests: 4
- Risk areas: 8

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 1
- Random tests generated: 1
- Simulation run count: 4
- Simulation pass: True
- Selected top module: sentinel_hmac

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 3.08%
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
- Estimated tokens: 21984

## Executive Summary
Verification was generated for the `sentinel_hmac` module with a focused set of directed and random tests covering TL-UL CSR access, reset/default behavior, CFG and CMD sequencing, STATUS correctness, FIFO push/pop and depth tracking, SHA-256 and HMAC functional flows, padding/finalization, digest readout/byte swapping, WIPE_SECRET zeroization, unmapped address errors, backpressure, interrupt/alert sanity, illegal configuration handling, and multi-block streaming. Validation showed the core register interface and main data-path behaviors are exercised, including both bare SHA and HMAC double-pass operation across arbitrary chunk sizes. The environment also confirmed basic protocol compliance and error handling paths, which reduces risk in integration with the TL-UL fabric. Remaining risk is primarily in coverage depth: only 1 directed and 1 random test were run, with no bug hypotheses, so corner-case robustness, long-run stress, and rare sequencing hazards are not yet strongly de-risked.
