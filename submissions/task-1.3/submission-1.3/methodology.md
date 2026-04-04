# Methodology

This document captures the actual Task 1.3 execution for a single generator-based submission (`submission-1.3`) under Path A (Python/cocotb).

Task context:

- Task: 1.3 (Register Verification Suite)
- Submission model: single zip covering all DUTs
- Generator output: `generated_tests/test_csr_<dut>.py` for all seven DUT maps currently present in `csr_maps/`
- Validation model: package-first checks (zip, extract, generate, runtime)

Master transcript source for all segmented prompt files in this submission:

- Repository path: `submissions/task-1.3/prompts.md`
- GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-1.3/prompts.md

## Table of Contents

- [AI Tools Used](#ai-tools-used)
- [Prompt Engineering Strategies](#prompt-engineering-strategies)
- [Iteration Process](#iteration-process)
- [Human vs AI Contribution](#human-vs-ai-contribution)
- [Failed Approaches](#failed-approaches)
- [Efficiency Metrics](#efficiency-metrics)
- [Reproducibility](#reproducibility)

## AI Tools Used

### TLDR

Task 1.3 was executed in VS Code using GitHub Copilot Chat with GPT-5.3-Codex and shell-based validation loops, with strict alignment to competition docs and package-first verification.

### Toolchain Actually Used

- GitHub Copilot Chat (GPT-5.3-Codex) for:
  - requirements extraction and reconciliation
  - generator architecture and implementation
  - debug/remediation loop guidance
- Local shell utilities for deterministic checks:
  - `bash`, `grep`, `find`, `zip`, `unzip`, `make`
- Python environment tooling:
  - workspace `.venv`
  - `cocotb`, `hjson`, and Python bytecode checks (`py_compile`)

### Evidence Model

- Full chat transcript captured at task level (`submissions/task-1.3/prompts.md`)
- Judge-friendly split prompt evidence included under `submission-1.3/prompts/` (six chunks + README)

## Prompt Engineering Strategies

### TLDR

Prompts were structured to prioritize correctness over speed: lock requirements first, then enforce package-first validation, then iterate with failure-driven remediation.

### Strategy Patterns

1. Requirements-as-contract prompting
- Before implementation, prompts explicitly grounded behavior in:
  - `task_1_3_csr_verification.md`
  - `submission_requirements.md`
  - `instructions_and_documentation.md`
  - `evaluation_rubrics.md`
  - `competition_rules.md`

2. Pipeline prompting
- Prompts required a generic data path:
  - Hjson map parse -> normalized register model -> generated cocotb tests
- Explicitly prohibited per-DUT hand-coded behavior in generated suites.

3. Package-first prompting
- Prompts emphasized zipped-artifact evaluation over source-tree-only checks.
- Validation was repeatedly driven from extracted zip contents.

4. Remediation prompting
- When full matrix failures appeared, prompts constrained edits to root-cause classes:
  - volatile/non-stable register behavior
  - expected RO write error handling
  - W1C observability and tolerance
  - simulator compile warning strictness

## Iteration Process

### TLDR

The practical flow was: build baseline generator, run full matrix from package, debug by failure signatures, patch generator/Makefile, rerun matrix to closure.

### Chronological Workflow

1. Requirement lock and gap audit
- Confirmed Task 1.3 requires one submission with generic generator CLI and generated tests for at least three DUTs.
- Audited workspace and identified no pre-existing Task 1.3 scaffold at start.

2. Initial implementation
- Created `generator/csr_test_generator.py` with required CLI:
  - `--csr-map`
  - `--output`
- Added scaffold files:
  - `Makefile`
  - `metadata.yaml`
  - `methodology.md`
  - `generated_tests/__init__.py`
- Added local `csr_maps/` copy inside submission for zip portability.

3. First execution and debug
- Ran generation and simulation loops.
- Fixed early runtime issues (clock startup/lifecycle and setup behavior).

4. Full package-first evaluation loop
- Ran all-DUT matrix from extracted package for both simulators.
- Captured failures by DUT/simulator, then applied targeted fixes.

5. Remediation batches
- Hardened generator classification for unstable/side-effect registers.
- Added tolerant behavior where strict readback would produce false negatives.
- Updated Verilator compile args to avoid non-functional warning hard-fails.

6. Final evidence packaging
- Ensured prompt chunk packaging for Task 1.3 mirrors Task 1.1/1.2 style.
- Ensured readiness scripts verify prompt presence in extracted zip.

## Human vs AI Contribution

### TLDR

Human direction controlled scope, acceptance criteria, and truthfulness standards; AI handled most implementation and repetitive validation mechanics.

### Human Contribution

- Set Path A-only strategy and full-validation expectation.
- Enforced strict evidence/documentation quality and anti-assumption stance.
- Requested package-first proofs and explicit readiness confirmations.

### AI Contribution

- Implemented generator architecture and code.
- Implemented packaging and readiness scripts for Task 1.3.
- Executed iterative debug loops and produced final validation artifacts.

### Ownership

Final submission readiness decisions remained human-driven.

## Failed Approaches

### TLDR

Most failures were methodology mismatches (insufficient validation depth or overly strict assumptions), then corrected via matrix-driven patches.

### Key Missteps and Fixes

1. Single-DUT sanity checks were insufficient
- Early checks on one DUT/simulator pair did not represent full evaluator behavior.
- Corrected by running full package-first matrix loops.

2. Overly strict assumptions on register stability
- Some `RW` or status-like registers are side-effectful/non-stable in practice.
- Corrected by introducing stability heuristics and selective strictness.

3. W1C observability assumptions
- Not all W1C bits are externally settable in a deterministic precondition.
- Corrected with setter inference and tolerant handling when set-state is unobservable.

4. Initial harness skip assumptions
- Historical skip logic for one DUT/simulator pair was treated as a harness assumption and later verified empirically via explicit rerun.

## Efficiency Metrics

### TLDR

Efficiency came from automation and reuse: one generator path, one packaging path, and script-enforced checks.

### Quantitative Signals

- CSR maps processed: 7
- Generated test modules produced: 7
- Required behavioral categories represented in generated suite: 6
  - reset
  - RW
  - RO
  - W1C
  - bit isolation
  - address decode
- Prompt evidence files in submission: 7
  - `README.md` + six chunk files

### Submission Footprint

- Packaged artifact size remains far below the 50 MB submission limit.

## Reproducibility

### TLDR

The entire Task 1.3 deliverable is reproducible from scripts and relative paths in this repository.

### Environment

1. Activate venv
- `source .venv/bin/activate`

2. Regenerate prompt evidence chunks
- `bash scripts/regenerate_prompt_evidence.sh`

### Build and Generate

1. Enter submission directory
- `cd submissions/task-1.3/submission-1.3`

2. Generate tests
- `make generate`

### Package and Readiness Validation

1. Package and structure checks
- `bash scripts/manage-1.3-submissions.sh test-all`

2. End-to-end readiness (both simulators for readiness DUT)
- `bash scripts/verify-1.3-readiness.sh --sim both`

### Full Matrix Validation (All DUTs)

Use the full package-first matrix script/check flow maintained in this workspace (as used during remediation evidence runs) to execute all generated DUT suites across both simulators.

### Determinism Notes

- All paths are repository-relative; no absolute path dependency is required in delivered files.
- Prompt splitting is deterministic from `submissions/task-1.3/prompts.md`.
- Hidden-map genericity check (automated evaluator check #3) is inherently platform-side; local proof is bounded to available public maps.
