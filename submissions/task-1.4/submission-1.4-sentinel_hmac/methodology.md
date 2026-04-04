# Methodology

This document records the actual Task 1.4 execution history for
submission-1.4-sentinel_hmac under Path A.

Task context:
- Task: 1.4 (Assertion Library)
- DUT: sentinel_hmac
- Assertion files: protocol, functional, structural, liveness
- Manifest count: 27 assertions (8 protocol, 6 functional, 7 structural, 6 liveness)

Master transcript source for prompt evidence:
- Repository path: submissions/task-1.4/prompts.md
- GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-1.4/prompts.md

## AI Tools Used

- GitHub Copilot (GPT-5.3-Codex) for assertion drafting, bind wiring, cocotb stimulus, and readiness script implementation.
- Local shell execution for compile-run-debug loops and ZIP-first validation.
- Workspace scripts for packaging and structure checks.

## Prompt Engineering Strategies

- Requirement-anchored prompting: translated Task 1.4 requirements into strict file/checkpoint targets.
- Category-first prompting: generated protocol and structural assertions first, then functional and liveness.
- Temporal-debug prompting: every failure was traced to cycle-level request-response semantics before patching.
- Simulator-compatibility prompting: favored conservative syntax and explicit sampling logic to avoid parser and timing ambiguities.

## Iteration Process

1. Audit and planning
- Audited workspace and identified missing Task 1.4 scaffolding and automation.
- Chose sentinel_hmac as one of two high-value DUTs for submission.

2. Initial implementation
- Created assertion modules, bind file, manifest, cocotb test, metadata, methodology, Makefile.

3. Debug and refinement
- Resolved protocol/liveness temporal mismatches discovered in Verilator.
- Updated checks to align with accepted-cycle response behavior where DUT logic is combinational.
- Re-ran both simulators until clean pass.

4. Packaging and readiness
- Added Task 1.4 manage and verify automation scripts.
- Added ZIP extraction structure checks and dual-simulator execution checks.
- Added prompt evidence chunk requirements into readiness validation.

## Human vs AI Contribution

- Human-led: scope, priorities, and acceptance gates.
- AI-led: implementation of assertions/tests/scripts and remediation loops.
- Joint: root-cause triage for temporal semantics and final submission hardening.

## Failed Approaches

- Next-cycle response assumptions in some assertions caused false positives and were replaced with timing-accurate checks.
- Overly strict liveness assumptions were relaxed into bounded, architecture-aligned progress checks.
- One-simulator confidence was rejected in favor of mandatory dual-simulator validation.

## Efficiency Metrics

- Major interaction rounds: audit/planning, scaffold, compatibility rework, temporal fixes, packaging automation.
- Assertions delivered: 27 for sentinel_hmac.
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
