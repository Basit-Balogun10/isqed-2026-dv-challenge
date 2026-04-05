# Methodology

Task 2.1 was executed as an evidence-first, audit-driven coverage gap analysis campaign across all seven DUTs in Path A.
The workflow followed the real conversation timeline: requirement audit, implementation of baseline coverage collection, structured gap extraction, compliance hardening, and strict re-audit before final packaging.

## AI Tools Used

- GitHub Copilot (GPT-5.3-Codex) for scripting, gap extraction logic, and report generation.
- Local shell tooling (`make`, `verilator_coverage`, Python in `.venv`) for baseline execution and artifact generation.
- Workspace search/read tooling for RTL/spec/vplan cross-references and compliance checks.

- Prompt evidence sources:
  - Master transcript: `submissions/task-2.1/prompts.md`
  - Split judge-friendly transcript chunks: `submissions/task-2.1/submission-2.1/prompts/`
  - Repository conversation URL: `https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-2.1/prompts.md`

## Prompt Engineering Strategies

- Audit-first prompting: started from Task 2.1 and submission-requirement sections before implementation.
- Evidence-constrained prompting: only accepted gaps with concrete `file` and `line_range` anchors tied to uncovered coverage data.
- Compatibility prompting: generated both primary Task 2.1 outputs and compatibility-format outputs to satisfy differing documentation expectations.
- Hardening prompts: repeatedly audited packaging/readiness outputs and patched mismatches until checks were green.

## Iteration Process

1. Ran a requirement audit pass and confirmed no existing Task 2.1 scaffold/scripts were present.
2. Attempted to reuse raw skeleton baseline tests; observed incompatibilities in that path and pivoted.
3. Implemented a self-contained baseline runner and collection pipeline under `baseline_runner/` and `analysis_scripts/`.
4. Executed all 7 DUTs to generate baseline coverage artifacts and summary reports.
5. Improved summarization (source-path normalization and uncovered-range prioritization) for stable, reviewer-friendly anchors.
6. Correlated uncovered RTL regions to spec/vplan intent and generated 28 structured major gaps.
7. Generated primary deliverables (`gap_analysis.yaml`, `gap_summary.md`, `closure_plan.md`) and compatibility outputs (`gap_analysis/*.md`, `summary.md`, `priority_table.yaml`).
8. Added and validated Task 2.1 management/readiness automation (`manage-2.1-submissions.sh`, `verify-2.1-readiness.sh`, unified readiness integration).
9. Performed a full compliance re-audit and fixed discovered issues (functional-bin table schema wording, reproducible generator output, and packaging guards against HDL/annotated RTL in ZIP).
10. Repackaged prompt evidence from the full master transcript into six chronological chunks with an index README for judge navigation.

Coverpoint/Bin mapping note (judge-margin clarification):

- For per-DUT functional-bin tables, `Coverpoint` is represented as `vp_scenario_id`, and `Bin Name` is the corresponding VP scenario ID token.
- This mapping was used because the available baseline artifacts did not include richer native functional coverage bin exports; VP scenario IDs were the most traceable and reproducible functional intent anchors.

## Human vs AI Contribution

- Human-led: objective setting (Path A, all-DUT scope), acceptance criteria, and final packaging decisions.
- AI-led: implementation of automation scripts, coverage parsing logic, structured report generation, and iterative compliance fixes.
- Joint: prioritization quality checks, root-cause sanity review, and final go/no-go readiness decisions.

## Failed Approaches

- Initial direct reuse of raw skeleton reference tests was unreliable in this workspace due interface/API mismatches; replaced with a self-contained baseline runner.
- Early coverage summaries used less reviewer-friendly source paths; canonicalization to `duts/<dut>/<dut>.sv` anchors was added.
- An intermediate bulk table edit accidentally touched non-target markdown sections; fixed with section-scoped correction and generator-level schema updates.
- Inline heredoc audit command flow was unreliable in this terminal wrapper; switched to deterministic temporary script execution for the strict audit pass.

## Efficiency Metrics

- DUTs analyzed: 7/7
- Structured major gaps reported: 28
- Primary required outputs generated: 3
- Compatibility outputs generated: per-DUT gap markdowns + summary + priority table
- Prompt evidence files in submission package: 7 markdown files (6 chunks + README)
- Readiness status: Task 2.1 verifier green (`--quick` and full)
- Final package includes no DUT RTL/annotated HDL files

## Reproducibility

Environment:

- Path A (cocotb + open-source flow)
- Python virtual environment: `.venv`

Core commands:

1. `source .venv/bin/activate`
2. `bash submissions/task-2.1/submission-2.1/analysis_scripts/collect_baseline_coverage.sh`
3. `python submissions/task-2.1/submission-2.1/analysis_scripts/summarize_coverage.py`
4. `python submissions/task-2.1/submission-2.1/analysis_scripts/generate_gap_deliverables.py`
5. `bash scripts/verify-2.1-readiness.sh --sim both`
6. `bash scripts/verify-readiness.sh 2.1 --quick --sim both`

Output set:

- Primary: `gap_analysis.yaml`, `gap_summary.md`, `closure_plan.md`
- Compatibility: `gap_analysis/*.md`, `summary.md`, `priority_table.yaml`
- Evidence: `prompts/README.md` + six split transcript files sourced from `submissions/task-2.1/prompts.md`
