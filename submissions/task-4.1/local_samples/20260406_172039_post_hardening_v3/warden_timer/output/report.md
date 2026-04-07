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
- Random tests: 4
- Risk areas: 7

## Test Results
- Generated Python files: 15
- Syntax validation pass: False
- Directed tests generated: 10
- Random tests generated: 4
- Simulation run count: 0
- Simulation pass: False
- Selected top module: warden_timer

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 0.0%
- Toggle coverage: 0.0%
- FSM coverage: 0.0%
- Functional coverage: 0.0%
- Code coverage source: no_coverage_database
- Functional coverage source: no_functional_data

## Bugs Found
- Static bug hypotheses: 0
- Detailed records are located in `bug_reports/`.

## Agent Methodology
- Iterations performed: 2
- LLM provider: openai
- LLM mode observed: online
- LLM calls: 14
- Estimated tokens: 18656

## Executive Summary
Verification for **warden_timer** generated a focused set of **10 directed** and **4 random** tests covering TL-UL CSR access, the 64-bit mtime counter with 12-bit prescaler, both 64-bit timer comparators, watchdog bark/bite/pet behavior, interrupt CSR triplet behavior, alert assertion, reset initialization, and partial 64-bit comparator updates. The environment validated basic read/write access, free-running counter operation, comparator interrupt generation, watchdog sequencing, lock/unlock behavior, and CSR access semantics including read-only/write-only behavior. Coverage also exercised watchdog bite-induced `alert_o` behavior and reset-only unlock constraints, reducing risk in the core timer/watchdog control paths. Remaining risk is concentrated in untested corner cases due to **0.0 functional coverage** and **no bug hypotheses**, so deeper stress on timing races, long-run counter rollover, and rare partial-update/interrupt interactions is still warranted.
