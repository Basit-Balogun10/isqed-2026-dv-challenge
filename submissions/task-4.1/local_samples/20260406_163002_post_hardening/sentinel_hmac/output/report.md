# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: sentinel_hmac
- Total RTL files: 1
- Total RTL lines: 796
- TL-UL detected: True
- Protocol hints: hmac
- Estimated FSM blocks: 4

## Verification Plan
- Planned features: 15
- Directed tests: 9
- Random tests: 5
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
- Functional coverage: 30.12%
- Code coverage source: no_coverage_database
- Functional coverage source: functional_bins_from_test_snapshots

## Bugs Found
- Static bug hypotheses: 0
- Detailed records are located in `bug_reports/`.

## Agent Methodology
- Iterations performed: 2
- LLM provider: openai
- LLM mode observed: online
- LLM calls: 20
- Estimated tokens: 37333

## Executive Summary
Verification was generated for the `sentinel_hmac` module, covering directed and random stimulus with 30.12 functional scenarios. The environment validated TL-UL CSR read/write compliance, CFG and CMD sequencing, STATUS reporting, FIFO/backpressure behavior, SHA-256 bare hash and HMAC key flows, padding/finalization, digest readout and byte-order handling, zeroization, invalid configuration handling, unmapped address responses, interrupt/alert smoke checks, reset recovery, and multi-block streaming. Overall, the generated tests exercised both nominal operation and key error/edge conditions, providing broad functional confidence in control, data path, and state-management behavior. No bug hypotheses were identified, which limits targeted risk reduction for latent corner-case issues. Remaining risk is concentrated in unproven deep corner cases and long-run interactions, especially around timing-sensitive FIFO pressure, reset/zeroization races, and rare configuration combinations not fully stressed by the current mix.
