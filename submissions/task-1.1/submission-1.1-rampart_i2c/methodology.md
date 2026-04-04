# Methodology

This file documents the actual Task 1.1 work for DUT `rampart_i2c` using evidence from the full chat transcript now split under `prompts/`.

Task context for this specific submission:

-   DUT: `rampart_i2c` (requires protocol-specific agenting)
-   Verification path: Path A (cocotb + Python, open-source simulators)
-   Required files delivered: `testbench/tl_ul_agent.py`, `testbench/scoreboard.py`, `testbench/coverage.py`, `testbench/env.py`, `tests/test_basic.py`, `Makefile`, `metadata.yaml`, `methodology.md`, `prompts/`
-   Additional protocol-oriented files present for this DUT: `testbench/protocol_agent.py`, `testbench/i2c_protocol_agent.py`, `testbench/i2c_environment.py`, `testbench/i2c_scoreboard.py`

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

The implementation was driven by agentic Copilot sessions under strong human direction, with repeated compliance checks against official competition docs and scripted local verification.

### Tooling Actually Used

-   GitHub Copilot chat in VS Code (agent execution, file edits, shell checks)
-   Competition-focused instruction artifacts maintained early and refined during execution:
    -   `AGENTS.md`
    -   `.claude/agents/*`
-   Scripted validation and packaging:
    -   `scripts/manage-1.1-submissions.sh`
    -   `scripts/test-1.1-submissions.sh`
    -   `scripts/verify-1.1-readiness.sh`

### DUT-Specific Notes

For `rampart_i2c`, work included both CSR/TL-UL flow and external protocol concerns, making this DUT the most protocol-intensive Task 1.1 target in the selected set.

## Prompt Engineering Strategies

### TLDR

Prompting moved from broad planning to strict requirement traceability, with repeated corrections to avoid assumption drift and to keep artifacts evaluator-aligned.

### Strategy Patterns Used

1. Requirement-first prompting
    - Every ambiguity was driven back to `submission_requirements.md`, task docs, and platform instructions.
2. Reuse-first architecture prompting
    - Build and stabilize TL-UL core once, then add DUT-specific protocol layers.
3. Validation-oriented prompting
    - Prefer prompts that request objective checks (file presence, extraction checks, dual-simulator runs) over subjective summaries.
4. Evidence-preserving prompting
    - Preserve full conversation evidence and improve reviewer navigation by splitting into ordered prompt chunks.

### Evidence Location

This submission includes full split transcript evidence in `prompts/`.

## Iteration Process

### TLDR

The work proceeded in loops: implement, validate, detect mismatch, patch scripts/docs, revalidate, and repackage.

### End-to-End Flow (What Happened)

1. Workspace and agent setup
    - Prompt files and agent instructions were customized for the challenge context.
2. Task 1.1 implementation pass
    - Core required files were generated and normalized.
3. Protocol emphasis for `rampart_i2c`
    - Added I2C-specific supporting files in addition to required Task 1.1 core files.
4. Compliance hardening
    - Repeatedly checked required-file completeness and toolchain assumptions.
5. ZIP-first readiness
    - Rebuilt and validated extracted ZIP contents with scripts.

### What Is Specific to `rampart_i2c`

-   Includes protocol-facing files beyond the minimal required set.
-   Retains mandatory core files expected by Task 1.1 checklists.
-   Uses the same evidence model (`prompts/`) as other DUTs for consistency.

## Human vs AI Contribution

### TLDR

AI accelerated drafting and bulk edits; human control determined strategy, scope, and compliance gates.

### AI Contribution

-   File drafting and directory normalization
-   Fast adaptation across multiple DUT submissions
-   Packaging and status command execution

### Human Contribution

-   Directed correction of non-compliant assumptions
-   Enforced exhaustive scope and no artificial time constraints
-   Requested stricter evidence quality and truthful methodology narrative

### Review Discipline

All generated artifacts were considered provisional until validated through scripted checks and document traceability.

## Failed Approaches

### TLDR

The major failures were process-level, not syntax-level: scope assumptions, path interpretation confusion, and evidence formatting quality.

### Key Failures and Corrections

1. Artificial prioritization language
    - Failure: introducing "if time permits" style planning.
    - Correction: explicit exhaustive execution rule in workspace instructions.
2. Path framing confusion
    - Failure: inconsistent interpretation language around verification path details.
    - Correction: explicit clarifications in workspace instruction files and checklist-driven execution.
3. Evidence readability gap
    - Failure: single-file prompt dump not judge-friendly.
    - Correction: split prompt transcript evidence into ordered chunk files with index.

## Efficiency Metrics

### TLDR

Process efficiency came from scriptable checks, reusable infrastructure, and consistent packaging structure.

### Concrete Metrics for This Submission

-   Task 1.1 tests in this DUT submission: 1 (`tests/test_basic.py`)
-   Required-core testbench files present: 4 (`tl_ul_agent.py`, `scoreboard.py`, `coverage.py`, `env.py`)
-   Protocol-oriented helper files additionally present: 4 (`protocol_agent.py`, `i2c_protocol_agent.py`, `i2c_environment.py`, `i2c_scoreboard.py`)
-   Prompt evidence files now present in this DUT submission: 7 files (`README.md` + 6 transcript chunks)
-   Source transcript size used for evidence generation (Task 1.1 master): 8422 lines

### Process Efficiency Wins

-   One shared TL-UL strategy reused across DUTs
-   ZIP extraction checks used as a pre-upload gate
-   Scripted status and readiness reduced manual inspection overhead

## Reproducibility

### TLDR

The submission is reproducible through checked-in scripts and deterministic evidence regeneration.

### Rebuild and Validate

1. Regenerate prompt evidence chunks
    - `bash scripts/regenerate_prompt_evidence.sh`
2. Verify Task 1.1 submission structure
    - `bash scripts/manage-1.1-submissions.sh verify`
3. Run readiness and reverse checks
    - `bash scripts/verify-1.1-readiness.sh --sim both`
4. Rebuild final ZIP artifacts
    - `bash scripts/manage-1.1-submissions.sh rebuild-all`

### Determinism Notes

-   Packaging scripts exclude transient build artifacts.
-   Evidence files are generated from versioned master transcripts.
-   Required-file checks are script-enforced and repeatable.
