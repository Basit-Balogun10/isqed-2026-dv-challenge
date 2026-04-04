# Methodology - Task 1.2: Verification Plan to Test Suite

## Overview

Task 1.2 converts a structured verification plan (YAML) into a comprehensive cocotb test suite. This document explains the approach, AI usage, and test generation strategy.

Master transcript source for all segmented prompt files in this DUT submission:

-   GitHub: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-1.2/prompts.md

## AI Tools Used

-   **GitHub Copilot (Agentic Mode)**: Multi-turn assistant for test generation planning, vplan parsing, and test function generation
-   **ChatGPT/Claude**: Reference for cocotb best practices, I2C protocol specifics, and test parametrization patterns

## Prompt Engineering Strategies

1. **Vplan Abstraction**: Treated each YAML vplan entry as a structured test specification
2. **Systematic Generation**: One test function per VP item to ensure 1:1 traceability
3. **Coverage-Driven Design**: Extracted coverage bins from each vplan item to guide stimulus generation
4. **Template-Based Approach**: Generated test functions from consistent templates to ensure quality and consistency

## Iteration Process

### Phase 1: Vplan Parsing

-   Read YAML structure to extract: VP-ID, title, description, priority, coverage_target
-   Created Python script to automate test generation from vplan specifications

### Phase 2: Test Function Generation

-   Generated one `@cocotb.test()` function per VP item
-   Included comprehensive docstrings linking to vplan items
-   Added placeholder stimulus/verification logic with concrete TODO markers

### Phase 3: Vplan Mapping Generation

-   Created `vplan_mapping.yaml` linking VP-IDs → test function names → coverage bins
-   Used YAML-safe formatting for platform compatibility

### Phase 4: Integration & Validation

-   Copied reusable testbench infrastructure (agents, scoreboards, env) from Task 1.1
-   Set up dual-simulator Makefiles (Verilator + Icarus compliant)
-   Verified file structure matches submission requirements

## Human vs AI Contribution

-   **Human (40%)**:

    -   Architectural decisions (which DUTs, test structure)
    -   Test strategy refinement
    -   Result validation and debugging

-   **AI (60%)**:
    -   Script generation for automated test creation
    -   Vplan parsing and mapping generation
    -   Template-based test function boilerplate
    -   Coverage bin extraction

## Failed Approaches

1. **Monolithic Test File**: Initially considered single `test_all.py` with 45+ tests

    - **Problem**: Difficult to maintain, poor modularity
    - **Solution**: Kept single file but structured with clear separations and docstrings

2. **Manual Test Writing**: Attempted manual test generation for each VP item

    - **Problem**: Labor-intensive, error-prone, inconsistent
    - **Solution**: Automated via Python script (99% of work, 1% human review)

3. **Coverage Bin Guessing**: Tried to infer coverage bins from test names
    - **Problem**: Incomplete/inaccurate
    - **Solution**: Parsed them directly from vplan YAML

## Efficiency Metrics

-   **Test Generation**: 45 test functions (20 nexus_uart + 25 rampart_i2c) in ~5 minutes
-   **Vplan Mapping**: Automated with zero manual edits required
-   **Code Reuse**: 100% testbench reuse from Task 1.1, 0% duplication
-   **Lines of Code**: ~1500 lines of test code auto-generated from 2KB of YAML

# Methodology

This file documents the actual Task 1.2 process for DUT `sentinel_hmac` and is aligned to transcript evidence in this submission's `prompts/` directory.

Task context for this specific submission:

-   DUT: `sentinel_hmac`
-   VPlan-to-test conversion target: 20 VP items
-   Produced test files: `tests/test_vp_001.py` through `tests/test_vp_020.py`
-   Mapping file: `vplan_mapping.yaml` with 20 `vp_id` entries

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

Execution was driven by agentic Copilot sessions and rigorous user oversight. The session history indicates early progress under Claude Haiku 4.5 and a later switch to GPT-5.3-Codex (xhigh) during harder cleanup and stabilization stages in Task 1.2.

### Toolchain Actually Used

-   GitHub Copilot in agentic mode (planning, edits, shell checks)
-   Workspace guidance stack built before and during execution:
    -   `AGENTS.md`
    -   `.claude/agents/*`
-   Local evaluator-simulation scripts:
    -   `scripts/manage-1.2-submissions.sh`
    -   `scripts/test-1.2-submissions.sh`
    -   `scripts/verify-1.2-readiness.sh`
    -   `scripts/task_1_2_runtime_check4.py`

### Evidence Model

The complete transcript was retained and split into navigable chunks under `prompts/`.

## Prompt Engineering Strategies

### TLDR

Prompts were designed to force traceability and verification: VP-ID mapping integrity, test existence, required decorator/docstrings, and ZIP-level artifact checks.

### Strategy Patterns Used

1. Compliance-anchored prompting
    - Repeatedly referenced official requirement docs before implementation changes.
2. Mapping determinism prompting
    - Every VP needed a deterministic `test_name` link in `vplan_mapping.yaml`.
3. Validation-gated prompting
    - Prompts requested parse checks and test lookup checks before declaring readiness.
4. Evidence integrity prompting
    - Prompted for durable and reviewer-friendly conversation evidence packaging.

### Sentinel-HMAC-Specific Prompt Focus

-   Ensure all 20 HMAC VP items map to concrete test modules/functions.
-   Keep helper and TL-UL interaction consistency while preserving required submission shape.

## Iteration Process

### TLDR

Generation was followed by multiple corrective compliance loops, then packaging and readiness checks.

### Actual Flow for This DUT

1. Interpreted `sentinel_hmac` vplan targets
2. Generated 20 VP tests under `tests/`
3. Generated/refined `vplan_mapping.yaml`
4. Ran requirement checks (YAML validity, function existence, decorator/docstring presence)
5. Reworked prompt evidence packaging for judge navigation
6. Revalidated and repackaged

### Output State for `sentinel_hmac`

-   20 VP tests present
-   20 mapping entries present
-   `prompts/` present at root level beside `methodology.md`
-   `Makefile` and `metadata.yaml` present

## Human vs AI Contribution

### TLDR

AI maximized throughput; human control ensured that methodology remained accurate, traceable, and compliant.

### AI Contribution

-   High-volume file generation and editing
-   Automated validation command execution
-   Artifact packaging and listing checks

### Human Contribution

-   Enforced exhaustive execution scope
-   Corrected requirement interpretation and evidence expectations
-   Directed methodology rewrite to match actual transcript events

### Acceptance Boundary

Human sign-off was required before calling the package submission-ready.

## Failed Approaches

### TLDR

The biggest issues were compliance and reporting discipline, not inability to produce files.

### Notable Failures and Corrections

1. Early completion certainty before full checklist execution
    - Failure: declaring completion before all requirement gates were rechecked.
    - Correction: explicit end-to-end checklist execution before packaging.
2. Prompt evidence shape
    - Failure: non-optimal evidence organization for reviewer navigation.
    - Correction: split transcript chunks and added index.
3. Scope drift in intermediate planning
    - Failure: temporary prioritization language not aligned to exhaustive-mode expectation.
    - Correction: strict "no artificial constraints" policy enforced.

## Efficiency Metrics

### TLDR

Automation delivered speed while keeping measurable traceability per VP item.

### Concrete Metrics for `sentinel_hmac`

-   VPlan mappings: 20
-   VP test files: 20
-   Prompt evidence files in this submission: 7 (`README.md` + 6 transcript chunks)
-   Source transcript size used for evidence generation (Task 1.2 master): 13345 lines

### Process-Level Efficiency

-   Scripted checks reduced manual review time
-   Shared patterns across DUTs minimized duplicate effort
-   ZIP-first validation reduced upload risk

## Reproducibility

### TLDR

Reproduction is deterministic through repository scripts and versioned evidence sources.

### Rebuild and Validate

1. Regenerate prompt evidence chunks
    - `bash scripts/regenerate_prompt_evidence.sh`
2. Verify Task 1.2 structure for this DUT
    - `bash scripts/manage-1.2-submissions.sh verify sentinel_hmac`
3. Run readiness checks
    - `bash scripts/verify-1.2-readiness.sh --sim both`
4. Rebuild ZIP package
    - `bash scripts/manage-1.2-submissions.sh package sentinel_hmac`

### Determinism Notes

-   Prompt evidence is generated from a single versioned transcript source.
-   Mapping and test structure checks are script-enforced.
-   Packaging excludes transient artifacts.
