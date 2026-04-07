# Methodology

## AI Tools Used

-   GitHub Copilot (GPT-5.3-Codex) as the primary analysis and implementation agent.
-   Local shell tooling for deterministic validation and evidence extraction (`grep`, `wc`, `awk`,
    `zip`, `unzip`, `git`).
-   Python standard-library validator (`preprocessing/log_parser.py`) for schema and field checks
    on all `analysis/failure_XX.yaml` files.

## Prompt Engineering Strategies

-   Audit-first prompting: start by forcing requirement extraction from `README.md`,
    `instructions_and_documentation.md`, `evaluation_rubrics.md`,
    `task_3_1_log_whisperer.md`, `competition_rules.md`, and
    `submission_requirements.md` before writing any deliverable files.
-   Evidence-first prompting: require extraction of decisive `UVM_ERROR` context, then correlate
    with specific RTL line ranges before assigning classification/root module.
-   Schema-lock prompting: enforce the exact Task 3.1 YAML shape from
    `submission_requirements.md` even when richer examples exist elsewhere.
-   Adversarial re-check prompting: perform a second pass that attempts to disprove initial
    classifications using DUT specs/RTL (used to reclassify several borderline cases).
-   Packaging compliance prompting: explicitly verify prompt chunking, README source URL, and ZIP
    payload contents as first-class requirements, not documentation afterthoughts.

## Iteration Process

1. Performed a full kickoff audit and planning pass, including scoring-impact analysis for
   automated fields (`classification`, `root_module`) and judge-scored narrative fields.
2. Profiled all 10 logs (918 total lines), extracted failure signatures, and created a
   first-pass hypothesis matrix.
3. Mapped each failure to concrete RTL regions across all 7 DUT top modules, then drafted
   `analysis/failure_01.yaml` through `analysis/failure_10.yaml`.
4. Authored `summary.md`, `methodology.md`, `metadata.yaml`, `Makefile`, and
   `preprocessing/log_parser.py`.
5. Implemented Task 3.1 automation scripts:
    - `scripts/manage-3.1-submissions.sh`
    - `scripts/verify-3.1-readiness.sh`
    - Task 3.1 integration in `scripts/verify-readiness.sh`
    - Task 3.1 integration in `scripts/regenerate_prompt_evidence.sh`
6. Ran package/readiness checks; then executed a deep quality audit of all 10 YAML analyses
   against full log context plus DUT specs.
7. Reclassified and corrected borderline analyses based on stronger evidence from specs/RTL,
   including updates to `failure_01.yaml`, `failure_04.yaml`, `failure_09.yaml`,
   `failure_10.yaml`, and `summary.md`.
8. Re-ran full validation chain until green:
   `manage-3.1-submissions.sh test-all`, `verify-3.1-readiness.sh --sim both`, and
   `verify-readiness.sh 3.1 --sim both`.
9. After user-provided updated master transcript, regenerated prompt chunks and refreshed
   prompt evidence packaging for Task 3.1.

## Human vs AI Contribution

-   Human-led (approximately 20%):
    -   Priority and risk decisions for ambiguous classifications.
    -   Final acceptance criteria for what counts as submission-ready.
-   AI-led (approximately 80%):
    -   High-volume evidence extraction from logs/specs/RTL.
    -   Drafting and revising all 10 structured analyses.
    -   Producing automation scripts, validator, summary, methodology, and prompt evidence
        packaging updates.

## Failed Approaches

-   Classifying solely from first `UVM_ERROR` lines produced incorrect confidence in root cause
    for edge cases.
-   Treating all failures as RTL logic bugs created mislabels where configuration/checker behavior
    better explained the observed failure.
-   Using task-page example structure as the primary schema risked parser mismatch; this was
    corrected by locking to `submission_requirements.md` exact Task 3.1 format.
-   Early timeout/NACK assumptions in I2C analysis were corrected after explicit check of timeout
    enable bit semantics and interrupt-bit mapping.

## Efficiency Metrics

-   Logs analyzed: 10/10
-   Total log lines processed: 918
-   RTL scope inspected: all 7 DUT top modules (5,437 total RTL lines)
-   Structured analyses produced: 10 (`failure_01.yaml` .. `failure_10.yaml`)
-   Prompt evidence packaged: master transcript + 6 chunk files + README
-   New automation delivered: 2 Task 3.1 scripts + dispatcher/regeneration integrations
-   Validation loops executed repeatedly until green (package, readiness, dispatcher)
-   Runtime dependencies introduced: none beyond Python standard library

## Reproducibility

From repository root:

1. `source .venv/bin/activate`
2. Regenerate prompt evidence chunks from the latest master transcript:
   `bash scripts/regenerate_prompt_evidence.sh`
3. Run package integrity flow:
   `bash scripts/manage-3.1-submissions.sh test-all`
4. Run ZIP-first readiness:
   `bash scripts/verify-3.1-readiness.sh --sim both`
5. Run unified readiness dispatcher:
   `bash scripts/verify-readiness.sh 3.1 --sim both`
6. Optional direct YAML validation:
   `python submissions/task-3.1/submission-3.1/preprocessing/log_parser.py --validate submissions/task-3.1/submission-3.1/analysis`

Prompt evidence source:

-   Repository path: `submissions/task-3.1/prompts.md`
-   Chunked evidence under `submission-3.1/prompts/`
