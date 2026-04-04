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

This file documents the actual Task 1.2 process for DUT `rampart_i2c` and is aligned to transcript evidence in this submission's `prompts/` directory.

Task context for this specific submission:

-   DUT: `rampart_i2c`
-   VPlan-to-test conversion target: 25 VP items
-   Produced test files: `tests/test_vp_001.py` through `tests/test_vp_025.py`
-   Mapping file: `vplan_mapping.yaml` with 25 `vp_id` entries

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

Task 1.2 execution was done through long-form agentic sessions in VS Code. Per operator notes and transcript timeline, early work started under Claude Haiku 4.5 and later switched to GPT-5.3-Codex (xhigh) during stabilization and cleanup.

### Toolchain Actually Used

-   GitHub Copilot agentic workflow in VS Code
-   Preconfigured instruction and helper-agent setup:
    -   `AGENTS.md`
    -   `.claude/agents/*`
-   Compliance and runtime validation scripts:
    -   `scripts/manage-1.2-submissions.sh`
    -   `scripts/test-1.2-submissions.sh`
    -   `scripts/verify-1.2-readiness.sh`
    -   `scripts/task_1_2_runtime_check4.py`

### Rampart-I2C-Specific Notes

`rampart_i2c` carried the largest VP volume among selected Task 1.2 DUTs, so it served as the stress case for mapping consistency and runtime coverage checks.

## Prompt Engineering Strategies

### TLDR

Prompting was centered on strict VP traceability and script-verifiable outputs, with repeated enforcement of evaluator-aligned checks.

### Strategy Patterns Used

1. VP item to test function mapping discipline
    - Every VP item required a concrete test function target and mapping entry.
2. Decorator and docstring enforcement
    - Prompts required `@cocotb.test()` and VP-ID references for traceability.
3. Runtime-check integration
    - Prompt flow included execution of runtime check scripts to align claimed coverage bins with observed execution records.
4. ZIP payload verification
    - Prompt flow required checking extracted ZIP structure, not only source trees.

### Rampart-I2C-Specific Prompt Focus

-   Sustain consistency across 25 VP tests and 25 mapping entries.
-   Keep helper abstractions (`tests/helpers.py`) aligned with TL-UL driving behavior.

## Iteration Process

### TLDR

The process iterated through generation, hard checks, evidence correction, and re-packaging until compliance stabilized.

### Actual Flow for This DUT

1. Parsed and interpreted `rampart_i2c` VPlan targets
2. Generated 25 VP test modules under `tests/`
3. Built and validated `vplan_mapping.yaml`
4. Executed evaluator-style checks (mapping parse, function existence, runtime checks)
5. Corrected evidence packaging and reran readiness scripts

### Output State for `rampart_i2c`

-   25 VP test files present
-   25 mapping entries present
-   `prompts/` evidence colocated with `methodology.md`
-   `Makefile` and `metadata.yaml` present

## Human vs AI Contribution

### TLDR

AI performed high-volume generation and checking; human leadership controlled truthfulness, scope expansion, and final release gates.

### AI Contribution

-   Bulk generation and updates for tests/mapping/documentation
-   Script execution loops for static and runtime checks
-   Repackaging and artifact status checks

### Human Contribution

-   Corrected strategic and compliance drift
-   Enforced exhaustive completion and no fabricated claims
-   Directed evidence restructuring for judge usability

### Quality Gate Ownership

Final go/no-go decisions were made by the human operator after script-backed verification.

## Failed Approaches

### TLDR

Primary issues were not code syntax defects, but workflow and compliance sequencing problems.

### Notable Failures and Corrections

1. Initial narrow DUT focus in early task flow
    - Failure: workflow temporarily centered on fewer DUTs before broad normalization.
    - Correction: expanded and synchronized submissions to full selected DUT set.
2. Prompt evidence packaging quality gap
    - Failure: less navigable evidence layout.
    - Correction: split, indexed transcript chunks in `prompts/`.
3. Premature completion signals during long loops
    - Failure: completion language before full checklist closure.
    - Correction: enforce final-check script execution before packaging.

## Efficiency Metrics

### TLDR

Despite heavy VP volume, automation made the process manageable and measurable.

### Concrete Metrics for `rampart_i2c`

-   VPlan mappings: 25
-   VP test files: 25
-   Prompt evidence files in this submission: 7 (`README.md` + 6 transcript chunks)
-   Source transcript size used for evidence generation (Task 1.2 master): 13345 lines

### Process-Level Efficiency

-   Automated mapping checks and runtime checks reduced manual review burden
-   Reused common testbench elements to avoid per-DUT rebuild overhead
-   Script-first readiness and packaging reduced zip-content mistakes

## Reproducibility

### TLDR

This submission can be rebuilt and revalidated from repository scripts and prompt sources.

### Rebuild and Validate

1. Regenerate prompt evidence chunks
    - `bash scripts/regenerate_prompt_evidence.sh`
2. Validate Task 1.2 structure
    - `bash scripts/manage-1.2-submissions.sh verify rampart_i2c`
3. Run readiness checks
    - `bash scripts/verify-1.2-readiness.sh --sim both`
4. Rebuild ZIP package
    - `bash scripts/manage-1.2-submissions.sh package rampart_i2c`

### Determinism Notes

-   Prompt chunk generation is deterministic.
-   Mapping parse and test-existence checks are script-enforced.
-   Packaging excludes transient build artifacts.
