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
- Simulation run count: 3
- Simulation pass: True
- Selected top module: sentinel_hmac

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 0.0%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 34.94%
- Code coverage source: no_coverage_database
- Functional coverage source: functional_bins_from_test_snapshots

## Bugs Found
- Static bug hypotheses: 0
- Detailed records are located in `bug_reports/`.

## Agent Methodology
- Iterations performed: 2
- LLM provider: openai
- LLM mode observed: online
- LLM calls: 18
- Estimated tokens: 31420

## Executive Summary
Verification was generated for the `sentinel_hmac` module, covering 34.94% functional closure with 1 directed and 1 random test. The validation scope exercised TL-UL CSR read/write compliance, reset/default CSR behavior, CFG mode selection, invalid configuration handling, W1S command semantics, FIFO status reporting, streaming message ingress, SHA-256/HMAC processing, endian/digest swap behavior, interrupt/alert sanity, unmapped address errors, handshake backpressure, zeroization, and partial/multi-block message support. Results indicate the core register interface, data path sequencing, and security-sensitive wipe/zeroization behavior were validated across both SHA-only and HMAC flows. Remaining risk is primarily coverage-related: with only modest functional closure and limited stimulus depth, corner cases in long-message sequencing, rare backpressure interactions, and configuration transitions may still be underexplored. No explicit bug hypotheses were reported, which reduces known defect risk but does not eliminate residual verification gaps.
