# Methodology

This file documents the actual Task 1.1 work for DUT `sentinel_hmac` using evidence from the full chat transcript now split under `prompts/`.

Task context for this specific submission:

-   DUT: `sentinel_hmac` (CSR-only interface for Task 1.1 protocol-agent requirements)
-   Verification path: Path A (cocotb + Python, open-source simulators)
-   Required files delivered: `testbench/tl_ul_agent.py`, `testbench/scoreboard.py`, `testbench/coverage.py`, `testbench/env.py`, `tests/test_basic.py`, `Makefile`, `metadata.yaml`, `methodology.md`, `prompts/`

Master transcript source for all segmented prompt files in this DUT submission:

-   GitHub: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-1.1/prompts.md

## Table of Contents

-   [AI Tools Used](#ai-tools-used)
-   [Prompt Engineering Strategies](#prompt-engineering-strategies)
-   [Iteration Process](#iteration-process)
-   [Human vs AI Contribution](#human-vs-ai-contribution)
-   [Failed Approaches](#failed-approaches)
-   [Efficiency Metrics](#efficiency-metrics)
-   [Reproducibility](#reproducibility)

## AI Tools Used

### TLDR

The submission was produced through agentic Copilot-driven implementation with strong human correction and compliance steering.

### Tooling Actually Used

-   GitHub Copilot chat in VS Code (planning, edits, shell execution)
-   Workspace instruction and helper-agent setup:
    -   `AGENTS.md`
    -   `.claude/agents/*`
-   Local compliance automation:
    -   `scripts/manage-1.1-submissions.sh`
    -   `scripts/test-1.1-submissions.sh`
    -   `scripts/verify-1.1-readiness.sh`

### DUT-Specific Notes

Because `sentinel_hmac` is CSR-only in this phase, the effort centered on bus-level transaction integrity, scoreboard expectations, and complete required structure rather than external protocol-line driving.

## Prompt Engineering Strategies

### TLDR

Prompts were progressively tightened from exploration prompts into strict requirement-anchored execution prompts with explicit verification steps.

### Strategy Patterns Used

1. Reference-before-action
    - Read official competition docs first on ambiguity.
2. Explicit structure prompting
    - Force required-file completeness checks.
3. Verifiable-claim prompting
    - Prefer measurable outputs (counts, parse checks, build checks) over status-only language.
4. Evidence usability prompting
    - Replace large single transcript dump with chunked, indexed prompt evidence for reviewer navigation.

### Evidence Location

Full evidence is included in this submission under `prompts/` (six chunks plus index).

## Iteration Process

### TLDR

Implementation followed a loop of generation, validation, mismatch discovery, correction, and final packaging verification.

### End-to-End Flow (What Happened)

1. Setup and context ingestion
    - AI-agent environment and instructions were tailored for this competition.
2. Task 1.1 file generation and normalization
    - Required files were created and checked for all selected DUTs.
3. Compliance iterations
    - Requirement interpretation mistakes were identified and corrected.
4. Script-supported validation
    - Readiness scripts and reverse-testing scripts were used as gates before packaging.
5. Evidence and documentation hardening
    - Prompt evidence was restructured and methodology rewritten for truthful reporting.

### What Is Specific to `sentinel_hmac`

-   Core required Task 1.1 files are present and aligned with CSR-only expectations.
-   The same reproducible packaging and readiness flow is applied as for the other DUTs.

## Human vs AI Contribution

### TLDR

AI accelerated output generation; human direction prevented requirement drift and enforced correction loops.

### AI Contribution

-   Drafting and updating submission files
-   Running scripted checks and packaging commands
-   Performing repetitive consistency edits across DUT folders

### Human Contribution

-   Enforced strict authenticity and no over-claiming
-   Redirected process whenever assumptions diverged from official docs
-   Required exhaustive completion and explicit evidence quality

### Governance Model

Human sign-off was required at each compliance-critical stage (requirements interpretation, packaging, and readiness checks).

## Failed Approaches

### TLDR

Main failures were methodological and communication-related, not tooling-related.

### Key Failures and Corrections

1. Assumption-led planning language
    - Failure: introducing strategy language not explicitly requested.
    - Correction: enforce exhaustive scope and requirement-backed decisions.
2. Inconsistent path framing
    - Failure: confusion in interpretation during iterations.
    - Correction: concise path clarification and documentation hierarchy usage.
3. Evidence discoverability
    - Failure: one large prompt file was hard to navigate.
    - Correction: split and indexed prompt transcript evidence.

## Efficiency Metrics

### TLDR

Efficiency gains came from reuse and script automation, while still preserving strict compliance checks.

### Concrete Metrics for This Submission

-   Task 1.1 tests in this DUT submission: 1 (`tests/test_basic.py`)
-   Required-core testbench files present: 4 (`tl_ul_agent.py`, `scoreboard.py`, `coverage.py`, `env.py`)
-   Prompt evidence files now present in this DUT submission: 7 files (`README.md` + 6 transcript chunks)
-   Source transcript size used for evidence generation (Task 1.1 master): 8422 lines

### Process Efficiency Wins

-   Reusable TL-UL pattern across submissions
-   Script-driven ZIP readiness checks
-   Unified folder contracts reduced hand-editing errors

## Reproducibility

### TLDR

The workflow is repeatable and script-driven from repository state.

### Rebuild and Validate

1. Regenerate prompt evidence
    - `bash scripts/regenerate_prompt_evidence.sh`
2. Verify Task 1.1 structures
    - `bash scripts/manage-1.1-submissions.sh verify`
3. Perform readiness and simulation checks
    - `bash scripts/verify-1.1-readiness.sh --sim both`
4. Rebuild ZIP packages
    - `bash scripts/manage-1.1-submissions.sh rebuild-all`

### Determinism Notes

-   Prompt chunk generation is deterministic from source transcripts.
-   Packaging excludes transient artifacts.
-   Required-file checks are repeatable and tool-enforced.
