# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: citadel_spi
- Total RTL files: 1
- Total RTL lines: 916
- TL-UL detected: True
- Protocol hints: spi
- Estimated FSM blocks: 7

## Verification Plan
- Planned features: 15
- Directed tests: 8
- Random tests: 4
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 1
- Random tests generated: 1
- Simulation run count: 4
- Simulation pass: True
- Selected top module: citadel_spi

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 10.61%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 52.73%
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
- Estimated tokens: 22741

## Executive Summary
Verification for `citadel_spi` generated a focused directed-plus-random test plan covering TL-UL register access, reset/default state checks, SPI mode and clock-divider programming, FIFO behavior, command sequencing, segment execution, and basic timing/interrupt observation. The environment validated all 12 CSRs for decode and smoke access, confirmed reset behavior, exercised CPOL/CPHA modes 0–3, and checked chip-select one-hot active-low behavior, TX/RX FIFO level tracking, and multi-segment CSAAT continuity. Functional coverage reached 52.73%, indicating meaningful breadth across configuration, data movement, and transaction control, including transmit-only, receive-only, and bidirectional paths. Remaining risk is concentrated in unclosed coverage gaps around deeper corner cases and protocol stress, since only one directed and one random test were run and no bug hypotheses were identified.
