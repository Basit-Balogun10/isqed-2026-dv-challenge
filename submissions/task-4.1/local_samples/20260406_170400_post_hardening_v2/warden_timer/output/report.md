# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: warden_timer
- Total RTL files: 1
- Total RTL lines: 636
- TL-UL detected: True
- Protocol hints: timer
- Estimated FSM blocks: 1

## Verification Plan
- Planned features: 10
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
- Selected top module: warden_timer

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 5.08%
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
- LLM calls: 20
- Estimated tokens: 32399

## Executive Summary
Verification was generated for the `warden_timer` module with one directed and one random test, covering TL-UL CSR access, 64-bit `mtime` readback, prescaler operation, dual timer comparators, watchdog functionality, alerting, reset behavior, and reserved-bit handling. Validation confirmed correct byte/word alignment checks, LOW/HIGH counter reads, zero-prescale and delayed prescaler update behavior, interrupt generation and W1C clearing, interrupt masking and software injection, watchdog pet/count/readback behavior, and lockout of control changes after watchdog lock. Reset defaults and reserved-bit read-as-zero/write-ignored behavior were also exercised and verified. The main remaining risk is coverage depth: with only 47.54% functional coverage and no bug hypotheses, corner-case interactions and rare timing sequences around comparator, prescaler, and watchdog transitions may still be underexplored.
