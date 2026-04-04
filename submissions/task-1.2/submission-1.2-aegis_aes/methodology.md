# Methodology

This file documents the actual Task 1.2 process for DUT `aegis_aes` and is aligned to transcript evidence in this submission's `prompts/` directory.

Task context for this specific submission:

-   DUT: `aegis_aes`
-   VPlan-to-test conversion target: 20 VP items
-   Produced test files: `tests/test_vp_001.py` through `tests/test_vp_020.py`
-   Mapping file: `vplan_mapping.yaml` with 20 `vp_id` entries

Master transcript source for all segmented prompt files in this DUT submission:

-   GitHub: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-1.2/prompts.md

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

Task 1.2 execution was done through long-form agentic sessions in VS Code. Per operator notes and transcript timeline, early work started under Claude Haiku 4.5 and later switched to GPT-5.3-Codex (xhigh) during test generation stabilization and cleanup.

### Toolchain Actually Used

-   GitHub Copilot agentic workflow in VS Code (multi-step planning, code edits, shell execution)
-   Workspace instruction assets established before/during execution:
    -   `AGENTS.md`
    -   `.claude/agents/*`
-   Local automation scripts used as evaluator mirrors:
    -   `scripts/manage-1.2-submissions.sh`
    -   `scripts/test-1.2-submissions.sh`
    -   `scripts/verify-1.2-readiness.sh`
    -   `scripts/task_1_2_runtime_check4.py`

### Evidence Model

The full session transcript was preserved and split into navigable chunks under `prompts/` for judge review.

## Prompt Engineering Strategies

### TLDR

Prompting focused on traceability and compliance: one VP item to one test entry, script-verifiable mappings, and explicit checks for required evidence artifacts.

### Strategy Patterns Used

1. VPlan-as-contract prompting
    - Every VP item was treated as a contract requiring a test anchor and mapping entry.
2. Structure-enforced prompting
    - Prompts explicitly required `@cocotb.test()` and VP-ID docstring/reference for each test.
3. Validator-first prompting
    - Prompts asked for local checks mirroring evaluator logic (YAML parse, function existence, pass/fail gating, coverage check script).
4. Packaging-truth prompting
    - Prompts required checking ZIP payloads, not just source folders.

### AEGIS-Specific Prompt Focus

-   Ensure all 20 `aegis_aes` VP mappings resolve to existing test functions.
-   Maintain consistent test naming pattern `test_vp_XXX.py` for direct mapping checks.

## Iteration Process

### TLDR

The flow was: generate, validate, detect requirement gaps, patch evidence/scripts, revalidate, then package.

### Actual Flow for This DUT

1. Requirement ingestion
    - Task docs and submission requirements were reviewed repeatedly.
2. Generation pass
    - VP tests and mapping structure were generated and populated for this DUT.
3. Compliance audit
    - Additional checks were run to confirm mapping parseability and test linkage.
4. Evidence correction phase
    - Missing/weak LLM conversation evidence pattern was addressed by establishing a structured `prompts/` directory.
5. Script hardening and re-checks
    - Verification scripts were adjusted during the campaign to better enforce required artifacts and runtime checks.

### Output State for `aegis_aes`

-   `vplan_mapping.yaml` present and populated
-   20 VP test files present
-   `prompts/` colocated with `methodology.md`
-   `Makefile` and `metadata.yaml` present

## Human vs AI Contribution

### TLDR

AI generated and transformed artifacts at speed, while human guidance controlled acceptance criteria, truthfulness, and requirement interpretation.

### AI Contribution

-   Bulk creation/update of test and documentation artifacts
-   Fast script-driven compliance checks
-   Cross-DUT consistency updates

### Human Contribution

-   Corrected strategic drift (scope, assumptions, and compliance interpretation)
-   Enforced strict "no BS" documentation quality
-   Required direct alignment between transcript evidence and methodology statements

### Decision Ownership

The human operator made all final acceptance decisions for submission readiness.

## Failed Approaches

### TLDR

The key failures were process reliability issues, not syntax issues.

### Notable Failures and Corrections

1. Partial-scope focus during early Task 1.2 execution
    - Failure: initial concentration on fewer DUTs before broader rollout.
    - Correction: expanded and normalized artifacts to all selected submission DUTs.
2. Evidence packaging incompleteness
    - Failure: prompt evidence initially not in judge-friendly split format.
    - Correction: transcript split into ordered files with index.
3. Overconfident completion messaging during iterations
    - Failure: "complete" claims before full checklist closure.
    - Correction: explicit, scripted final checks before packaging.

## Efficiency Metrics

### TLDR

Efficiency came from automation and reuse, then was protected by strict final-check scripts.

### Concrete Metrics for `aegis_aes`

-   VPlan mappings: 20
-   VP test files: 20
-   Prompt evidence files in this submission: 7 (`README.md` + 6 transcript chunks)
-   Source transcript size used for evidence generation (Task 1.2 master): 13345 lines

### Process-Level Efficiency

-   Reused common helper patterns across DUT submissions
-   Used script-based mapping/test checks instead of manual file-by-file review
-   Rebuilt ZIP artifacts after documentation/evidence changes to avoid stale payloads

## Reproducibility

### TLDR

This submission can be regenerated and revalidated with repository scripts and deterministic evidence generation.

### Rebuild and Validate

1. Regenerate prompt evidence chunks
    - `bash scripts/regenerate_prompt_evidence.sh`
2. Validate Task 1.2 structure
    - `bash scripts/manage-1.2-submissions.sh verify`
3. Run readiness checks
    - `bash scripts/verify-1.2-readiness.sh --sim both`
4. Rebuild ZIP payloads
    - `bash scripts/manage-1.2-submissions.sh package-all`

### Determinism Notes

-   Prompt chunk generation is deterministic from `submissions/task-1.2/prompts.md`.
-   Mapping and test existence checks are script-enforced.
-   Packaging scripts exclude transient artifacts so upload payloads are stable.
