# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: warden_timer
- Total RTL files: 1
- Total RTL lines: 636
- TL-UL detected: True
- Protocol hints: timer
- Estimated FSM blocks: 1

## Verification Plan
- Planned features: 9
- Directed tests: 9
- Random tests: 3
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 9
- Random tests generated: 3
- Simulation run count: 4
- Simulation pass: True
- Selected top module: warden_timer

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 5.61%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 47.54%
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
- Estimated tokens: 24220

## Executive Summary
Verification was generated for the `warden_timer` module, covering a 15-register TL-UL CSR map, the 64-bit free-running `mtime` counter with 12-bit prescaler, both 64-bit timer comparators, watchdog control/lock behavior, interrupt triplet behavior, alert generation, reset behavior, and reserved/partial-write handling. A total of 12 tests were created, including 9 directed and 3 random, and they achieved 47.54% functional coverage. Validation confirmed the key architectural behaviors across CSR access, timer counting, comparator interrupt generation, watchdog bark/bite/pet sequencing, and alert assertion on bite threshold. No bug hypotheses were raised, which is encouraging, but the coverage level remains moderate and leaves residual risk around unexercised corner cases, especially in partial 64-bit write sequencing, lock interactions, and reset/RO-WO edge conditions.
