# AutoVerifier Report

## DUT Analysis Findings
- Modules discovered: bastion_gpio
- Total RTL files: 1
- Total RTL lines: 324
- TL-UL detected: True
- Protocol hints: gpio
- Estimated FSM blocks: 2

## Verification Plan
- Planned features: 19
- Directed tests: 18
- Random tests: 6
- Risk areas: 10

## Test Results
- Generated Python files: 15
- Syntax validation pass: True
- Directed tests generated: 1
- Random tests generated: 1
- Simulation run count: 4
- Simulation pass: True
- Selected top module: bastion_gpio

## Coverage Achieved
- Line coverage: 0.0%
- Branch coverage: 3.72%
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
- LLM calls: 20
- Estimated tokens: 38885

## Executive Summary
Verification was generated for the `bastion_gpio` module, covering a 12-register TL-UL-controlled GPIO block with direction, data out, synchronized data in, interrupt, masked-write, reset, and alert behavior. Validation included directed and random testing of 32-bit GPIO control, two-cycle input synchronization, per-pin edge/level interrupts, W1C state handling, interrupt enable gating, software interrupt injection, and atomic masked writes with readback checks. Basic TL-UL CSR access compliance and normal-operation alert stability were also exercised, along with multi-pin concurrent GPIO activity. Functional closure reached 52.73%, indicating substantial feature coverage but not full signoff. The main remaining risk is incomplete functional coverage, especially around corner-case interactions between concurrent GPIO activity, interrupt modes, and masked-write/reset sequencing, despite no bug hypotheses being raised.
