# Methodology

This document records the actual Task 1.4 execution history for
submission-1.4-rampart_i2c under Path A.

Task context:
- Task: 1.4 (Assertion Library)
- DUT: rampart_i2c
- Assertion files: protocol, functional, structural, liveness
- Manifest count: 26 assertions (8 protocol, 6 functional, 7 structural, 5 liveness)

Master transcript source for prompt evidence:
- Repository path: submissions/task-1.4/prompts.md
- GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-1.4/prompts.md

## AI Tools Used

- GitHub Copilot (GPT-5.3-Codex) for assertion drafting, bind wiring, cocotb stimulus, and readiness script implementation.
- Local shell execution for compile-run-debug loops and ZIP-first validation.
- Workspace scripts for packaging and structure checks.

## Prompt Engineering Strategies

- Requirement-anchored prompting: converted Task 1.4 requirements into concrete file-level deliverables before coding.
- Category-first prompting: generated protocol and structural assertions first (lowest false-positive risk), then functional and liveness.
- Temporal-debug prompting: after each failing assertion, constrained prompts to explain cycle-level cause and patch only timing semantics.
- Simulator-compatibility prompting: prioritized parser-safe constructs that still preserve assertion intent across open-source toolchains.

## Iteration Process

1. Audit and planning
- Audited repository for existing Task 1.4 assets.
- Selected rampart_i2c and sentinel_hmac as highest-value feasible pair.

2. Initial implementation
- Created Task 1.4 submission structure and assertion modules.
- Added bind file, assertion manifest, cocotb exercise test, metadata, methodology, Makefile.

3. Compatibility and correctness loop
- Resolved simulator parser limitations by using robust clocked assertion style where needed.
- Verified clean runs on Icarus and Verilator.
- Adjusted checker timing only when observed behavior showed false-positive risk.

4. Packaging and readiness automation
- Implemented Task 1.4 manage and verify scripts.
- Added ZIP-first extraction checks and dual-simulator execution checks.
- Added prompt evidence chunk verification into readiness logic.

## Human vs AI Contribution

- Human-led: task scoping, DUT prioritization, acceptance criteria, and final quality gates.
- AI-led: assertion and testbench code generation, bind wiring, script automation, and debug loop execution.
- Joint: temporal semantics review, false-positive prevention, and packaging evidence completeness.

## Failed Approaches

- Overly strict cycle assumptions were rejected where they could produce false positives on legal behavior.
- Direct dependence on parser-sensitive assertion syntax was reduced when compatibility issues surfaced.
- Single-simulator confidence was treated as insufficient; final signoff required dual-simulator clean pass.

## Efficiency Metrics

- Major interaction rounds: audit/planning, scaffold, compatibility rework, temporal fixes, packaging automation.
- Assertions delivered: 26 for rampart_i2c.
- Dual-simulator clean status: PASS on Icarus and Verilator in readiness flow.

## Reproducibility

Environment:
- Path A (cocotb + open-source simulators)
- Python virtual environment at .venv

Core commands:
1. source .venv/bin/activate
2. bash scripts/manage-1.4-submissions.sh test-all
3. bash scripts/verify-1.4-readiness.sh --sim both

Optional bug-seed campaign:
- bash scripts/verify-1.4-readiness.sh --sim both --bug-seeds 1,2,3

Notes:
- Assertion sources and bind_file.sv are compiled with DUT sources via VERILOG_SOURCES.
- Prompt evidence is generated from submissions/task-1.4/prompts.md and copied into each Task 1.4 submission prompts directory.
