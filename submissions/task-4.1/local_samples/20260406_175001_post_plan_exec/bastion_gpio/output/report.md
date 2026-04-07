# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: bastion_gpio
- Total RTL files: 1
- Total RTL lines: 324
- TL-UL detected: True
- Protocol hints: gpio
- Estimated FSM blocks: 2

## Verification Plan
- Planned features: 15
- Directed tests: 10
- Random tests: 4
- Risk areas: 6

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 10
- Random tests generated: 4
- Simulation run count: 4
- Simulation pass: True
- Selected top module: bastion_gpio

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 3.8%
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
- LLM calls: 14
- Estimated tokens: 20027

## Executive Summary
Verification was generated for the `bastion_gpio` module with a focused mix of 10 directed and 4 random tests, covering 52.73% functional closure. The environment validated TL-UL CSR read/write access, register map decode for 12 CSRs, reset behavior, masked-write atomicity, concurrent/back-to-back bus sequencing, and alert output smoke. Functional behavior was also checked for GPIO direction control, output drive and `gpio_oe_o` gating, input synchronization visibility, interrupt detection across edge and level modes, W1C clear semantics, `INTR_ENABLE` gating, and software interrupt injection. Per-pin independence was exercised across a representative subset and a full-width smoke, reducing risk of broad connectivity or aliasing issues. Remaining risk is concentrated in the unclosed functional space, especially corner-case interactions between interrupt modes, timing-sensitive input behavior, and any untested cross-register or multi-pin concurrency scenarios.
