# Methodology

## AI Tools Used

- GitHub Copilot Chat (GPT-5.3-Codex) as the primary agentic implementation assistant for requirements audit, trace analysis authoring, cocotb repro development, and submission automation.
- VS Code terminal tooling for structured evidence collection from docs, RTL, trace CSV windows, and script behavior (`grep`, `find`, `sed`, `awk`, `wc`, packaging/readiness commands).
- Local schema validation utility (`preprocessing/trace_validator.py`) and ZIP-first readiness scripts to verify parser-safe outputs before submission.

## Prompt Engineering Strategies

- Enforced an audit-first workflow before coding: extract authoritative requirements, inventory repository state, and produce a gap matrix.
- Prioritized submission-parser schema from `submission_requirements.md` when task-page examples used richer but conflicting naming dialects.
- Used failure-focused prompts: derive one temporal causal chain and one minimal standalone repro per trace/failure.
- Required hard grounding in implementation evidence: each trace entry had explicit cycle values plus `root_cause_file` and `root_cause_line` from DUT RTL.
- Applied iterative hardening prompts for infrastructure reliability: improve DUT path discovery in Makefile and remove verifier-only path injection for evaluator parity.

## Iteration Process

1. Performed full Task 3.2 requirements audit against official docs (`task_3_2_trace_detective.md`, `submission_requirements.md`, `evaluation_rubrics.md`, `instructions_and_documentation.md`, `competition_rules.md`).
2. Inventory-scanned workspace for existing Task 3.2 assets and identified missing scaffolding, scripts, and packaging hooks.
3. Collected cycle-level evidence from all five trace description/CSV inputs and correlated them with DUT RTL locations.
4. Implemented complete submission scaffold:
	 - `analysis/trace_01..05.yaml`
	 - `reproduction_tests/repro_01..05.py`
	 - `Makefile`, `metadata.yaml`, `summary.md`, `methodology.md`, `testbench/tl_ul_agent.py`, and validator.
5. Added Task 3.2 automation:
	 - `scripts/manage-3.2-submissions.sh`
	 - `scripts/verify-3.2-readiness.sh`
	 - integration updates in shared readiness/prompt-evidence scripts.
6. Ran ZIP-first readiness; identified and fixed DUT path resolution robustness by hardening Makefile auto-discovery and removing verifier-specific DUT path override.
7. Executed deep compliance audit and fixed a judge-facing quality issue by reordering all `signal_trace` chains to symptom-to-cause chronology.
8. Revalidated with schema checks and dual-simulator compile readiness, then regenerated prompt evidence chunks from the final 3.2 master transcript.

## Human vs AI Contribution

- Human:
	- Set execution direction and quality bar (audit-first, then full implementation).
	- Flagged evaluator-parity concern on explicit DUT path injection.
	- Required a strict section-by-section compliance audit before signoff.
- AI:
	- Produced end-to-end implementation artifacts and automation.
	- Performed iterative debugging/fixes in readiness infrastructure.
	- Executed repeated validation loops and packaged submission assets.
- Human-in-the-loop governance:
	- Reviewed assumptions, requested detours for robustness, and drove final compliance confirmation.

## Failed Approaches

- Treating verifier-only `DUT_PATH` injection as an acceptable fix initially made local readiness pass but risked evaluator mismatch; replaced with robust Makefile-side DUT discovery.
- Early signal-trace presentation used cause-to-symptom ordering; this was corrected to symptom-to-cause to match Task 3.2 expectations for dependency-chain narration.
- Relying on compact summary-style prompt chunks after master transcript expansion was insufficient; prompt evidence was regenerated directly from the full transcript.
- Over-emphasizing task-page narrative naming was rejected in favor of `submission_requirements.md` parser-safe naming (`trace_XX.yaml`, `repro_XX.py`).

## Efficiency Metrics

- 5/5 required analysis YAML files authored and schema-validated.
- 5/5 standalone cocotb reproduction tests implemented (one target bug mechanism per trace).
- 100% required Task 3.2 structure present in ZIP package checks.
- Dual-simulator compile readiness validated through both task-specific and dispatcher verification paths.
- Prompt evidence packaged as 1 master transcript + 6 chunk files + index README, matching established submission conventions.

## Reproducibility

- Reproduction tests are deterministic: explicit clock/reset setup, bounded polling loops, and mechanism-specific assertions.
- Build and readiness flow is scriptable and repeatable with:
	- `bash scripts/manage-3.2-submissions.sh test-all`
	- `bash scripts/verify-3.2-readiness.sh --sim both`
	- `bash scripts/verify-readiness.sh 3.2 --sim both`
- Analysis structure is enforced by `preprocessing/trace_validator.py`.
- Submission packaging excludes forbidden artifacts and produces a compact ZIP under `submissions/zips-3.2/`.
- Prompt evidence in `prompts/` is generated from the full master transcript `submissions/task-3.2/prompts.md`, with a README link to the corresponding repository URL.
