# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: citadel_spi
- Total RTL files: 1
- Total RTL lines: 916
- TL-UL detected: True
- Protocol hints: spi
- Estimated FSM blocks: 7

## Verification Plan
- Planned features: 17
- Directed tests: 10
- Random tests: 3
- Risk areas: 8

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
- Functional coverage: 45.45%
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
- Estimated tokens: 23957

## Executive Summary
Verification was generated for the `citadel_spi` module, covering both directed and random stimulus in a 60-minute autonomous run. The environment validated TL-UL CSR access, reset/default state behavior, SPI mode operation across CPOL/CPHA 0–3, clock divider and chip-select timing, FIFO and command sequencing, CSAAT chaining, data-path integrity, and basic interrupt/alert responses. Functional coverage reached 45.45%, indicating meaningful feature exercise but not exhaustive closure. No bug hypotheses were raised, and no major functional escapes were observed in the tested scenarios. Remaining risk is concentrated in unclosed coverage areas, especially deeper FIFO boundary stress, corner-case timing interactions, and broader transaction permutations beyond the current smoke and basic stress scope.
