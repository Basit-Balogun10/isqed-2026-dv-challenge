# Methodology

This file documents the actual Task 1.1 work for DUT `aegis_aes` using evidence from the full chat transcript now split under `prompts/`.

Task context for this specific submission:

-   DUT: `aegis_aes` (CSR-only interface)
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

Primary authoring and execution was done through agentic GitHub Copilot sessions, with user-driven direction and corrections. For Task 1.1 specifically, most interactions were on the earlier model setup (Claude Haiku 4.5 era), with strict human oversight on competition compliance.

### Tooling Actually Used

-   GitHub Copilot chat in VS Code (agentic workflow, with shell and file-edit actions)
-   Workspace-level instruction files maintained during setup:
    -   `AGENTS.md`
    -   `.claude/agents/code-reviewer.md`
    -   `.claude/agents/prompt-engineer.md`
    -   `.claude/agents/systematic-debugger.md`
    -   `.claude/agents/test-writer.md`
-   Shell scripts used as local pipeline simulators and checkers:
    -   `scripts/manage-1.1-submissions.sh`
    -   `scripts/test-1.1-submissions.sh`
    -   `scripts/verify-1.1-readiness.sh`

### DUT-Specific Notes

`aegis_aes` is CSR-only for Task 1.1 protocol-agent requirements, so the work emphasized:

-   TL-UL transaction driving/monitoring
-   CSR-oriented scoreboard prediction and comparison
-   Environment wiring and coverage collection hooks

## Prompt Engineering Strategies

### TLDR

The prompting strategy evolved from broad planning to strict requirement-traceable execution. After detecting drift and assumption errors, prompts were re-centered around exact competition docs and checklists.

### Strategy Patterns Used

1. Document-first grounding
    - Repeatedly loaded `README.md`, `platform_content/instructions_and_documentation.md`, `platform_content/submission_requirements.md`, and task-specific docs before implementation.
2. Constraint reinforcement
    - Prompts were adjusted to stop "time budget" assumptions and enforce exhaustive scope unless explicitly narrowed by user.
3. Artifact checklist prompting
    - Prompts explicitly asked for required-file verification and ZIP-content verification, not only code generation.
4. Reverse-testing prompts
    - Prompts requested local reenactment of evaluator behavior (package ZIP, extract, validate, run).

### Evidence Location

The full sequence is preserved in this submission's `prompts/` directory (split transcript chunks and index file).

## Iteration Process

### TLDR

Task 1.1 was iterative: setup, implementation, compliance checks, corrections, packaging hardening, and re-validation.

### End-to-End Flow (What Happened)

1. Environment and agent setup
    - AI-agent instruction files were customized for this DV competition context.
2. Requirement interpretation and path clarification
    - Path A vs Path B confusion surfaced and was corrected through repeated doc checks and `AGENTS.md` refinements.
3. Submission implementation
    - Required Task 1.1 files were created or fixed for `aegis_aes`.
    - For this DUT (CSR-only), no external protocol agent was mandated.
4. Verification-script hardening
    - Packaging and readiness scripts were used and revised to reduce mismatch risk between local state and upload artifacts.
5. ZIP-first validation
    - Submission ZIPs were rebuilt and inspected through scripted checks.

### What Is Specific to `aegis_aes`

-   `tests/test_basic.py` exists and is the required smoke entry point.
-   `testbench/env.py`, `testbench/scoreboard.py`, and `testbench/coverage.py` were verified as present and integrated.
-   The `prompts/` evidence is colocated at the same level as `methodology.md` as required.

## Human vs AI Contribution

### TLDR

AI handled rapid drafting and script-scale edits; human leadership enforced truthfulness, constraints, scope, and final acceptance criteria.

### AI Contribution

-   Rapid drafting of testbench/support files and script updates
-   Bulk consistency updates across multiple submission folders
-   Packaging and readiness command execution

### Human Contribution

-   Set non-negotiable constraints (no fake claims, exhaustive scope, no artificial time limits)
-   Required repeated compliance re-checks against official docs
-   Directed restructuring of evidence (`prompts/`) and authenticity of `methodology.md`

### Responsibility Boundary

All final acceptance decisions were human-driven. AI output was treated as draft output until validated by script and document checks.

## Failed Approaches

### TLDR

Several workflow errors were encountered and corrected; documenting these was essential to avoid repeating them.

### Key Failures and Corrections

1. Assumption drift on scope and prioritization
    - Failure: introducing non-requested time-budget tradeoffs.
    - Correction: explicit "exhaustive unless user narrows scope" policy.
2. Path interpretation confusion (A vs B language)
    - Failure: inconsistent framing during early iterations.
    - Correction: explicit, concise guidance embedded in workspace instructions and repeatedly enforced by doc checks.
3. Evidence formatting shortcomings
    - Failure: single-file prompt evidence and weak navigability.
    - Correction: split transcript evidence into ordered chunk files with an index.

## Efficiency Metrics

### TLDR

Efficiency came from reusable TL-UL infrastructure, script automation, and repeated ZIP-first checks.

### Concrete Metrics for This Submission

-   Task 1.1 tests in this DUT submission: 1 (`tests/test_basic.py`)
-   Required-core testbench files present: 4 (`tl_ul_agent.py`, `scoreboard.py`, `coverage.py`, `env.py`)
-   Prompt evidence files now present in this DUT submission: 7 files (`README.md` + 6 transcript chunks)
-   Source transcript size used for evidence generation (Task 1.1 master): 8422 lines

### Process Efficiency Wins

-   Reused TL-UL agent pattern across DUTs instead of per-DUT reinvention
-   Used scripted readiness checks rather than manual folder inspection
-   Standardized packaging pathing and status outputs to reduce operator mistakes

## Reproducibility

### TLDR

This submission can be rebuilt and revalidated deterministically from workspace scripts and checked files.

### Rebuild and Validate

1. Regenerate prompt evidence chunks (if needed)
    - `bash scripts/regenerate_prompt_evidence.sh`
2. Verify Task 1.1 structure and readiness
    - `bash scripts/manage-1.1-submissions.sh verify`
    - `bash scripts/verify-1.1-readiness.sh --sim both`
3. Rebuild ZIP artifacts
    - `bash scripts/manage-1.1-submissions.sh rebuild-all`

### Determinism Notes

-   File structure checks are deterministic.
-   Packaging scripts exclude common transient artifacts (`sim_build`, `obj_dir`, `__pycache__`).
-   Prompt evidence is generated directly from versioned master transcripts, then copied into each DUT submission.
