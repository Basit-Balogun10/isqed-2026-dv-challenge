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
- Directed tests: 10
- Random tests: 4
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 10
- Random tests generated: 4
- Simulation run count: 4
- Simulation pass: True
- Selected top module: citadel_spi

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 10.79%
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
- Estimated tokens: 25095

## Executive Summary
Verification for `citadel_spi` generated a focused set of directed and random tests covering TL-UL register access, reset/default state, SPI mode and clock-divider programming, chip-select behavior, FIFO operation, segment execution, CSAAT chaining, interrupts, timing knobs, and basic transaction sequencing. The environment validated protocol sanity, register programming, data path behavior for TX/RX, MOSI/MISO ordering, and error handling for underflow/overflow and command FIFO overflow. Coverage reached 52.73% functional, with 10 directed and 4 random tests executed and no bug hypotheses raised. The main remaining risk is incomplete functional closure, especially around corner-case timing, deeper stress on chained/busy transactions, and broader negative testing beyond the exercised smoke and sanity scenarios.
