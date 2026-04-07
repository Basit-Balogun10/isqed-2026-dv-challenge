# Methodology

This document records the actual Task 3.3 execution flow for `submission-3.3` under Path A, including implementation, post-build audit, and submission hardening.

Master prompt transcript source:

-   Repository path: `submissions/task-3.3/prompts.md`
-   GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-3.3/prompts.md

## AI Tools Used

-   GitHub Copilot Chat (GPT-5.3-Codex) as the primary implementation assistant for requirement audit, bucketing synthesis, root-cause writing, and packaging automation.
-   Python + YAML parsing for deterministic extraction from:
    -   `phase3_materials/task_3_3_regression/failure_details.yaml`
    -   `phase3_materials/task_3_3_regression/test_manifest.yaml`
    -   `phase3_materials/task_3_3_regression/patches/patch_01.diff` to `patch_05.diff`
-   Shell tooling (`find`, `grep`, `zip`, `unzip`, `make`, readiness scripts) for ZIP-first validation and compliance checks.

## Prompt Engineering Strategies

-   Audit-first gating: no artifact writing until requirements were cross-checked in task doc, submission requirements, rubrics, instructions, and rules.
-   Schema-first strategy: treated `submission_requirements.md` as canonical parser contract when task-page narrative used a richer but different naming dialect.
-   Signal-family clustering: grouped failures by DUT + component + symptom signature to avoid per-test overfitting.
-   Evidence-separation strategy: explicitly separated "submission-structure pass" from "score-confidence risk" during final audits.
-   ZIP-first parity: validated packaged/extracted artifacts, not only source-tree artifacts, before declaring readiness.

## Iteration Process

1. Performed full Task 3.3 audit and produced an implementation plan.
2. Ingested Task 3.3 failure and patch metadata; quantified 35 failing tests and DUT-level distribution.
3. Created `submission-3.3/` scaffold and authored required outputs:
    - `bucketing.yaml`
    - `bug_descriptions.yaml`
    - `priority_ranking.yaml`
    - `patch_validation.yaml`
4. Added compatibility files for task-page naming drift:
    - `root_causes.md`
    - `priority.yaml`
5. Built validation and packaging infrastructure:
    - `analysis_scripts/validate_task33.py`
    - `Makefile`
    - `scripts/manage-3.3-submissions.sh`
    - `scripts/verify-3.3-readiness.sh`
    - integration updates to `scripts/verify-readiness.sh`, `scripts/README.md`, and `scripts/regenerate_prompt_evidence.sh`
6. Executed readiness loops (validator, compile gate, package/extract/verify, ZIP-first readiness).
7. Performed deep requirement-by-requirement audit against Task 3.3 docs and submission schema.
8. Regenerated prompt-evidence chunks from the full Task 3.3 master transcript and synchronized prompts README link.

## Human vs AI Contribution

-   Human contributions:
    -   Drove workflow sequence (audit first, then execute, then full-blown compliance audit).
    -   Required explicit readiness proof before submission.
    -   Requested organizer communication draft for input-availability clarification.
-   AI contributions:
    -   Implemented all Task 3.3 artifacts and validation scripts.
    -   Ran and interpreted packaging/readiness checks.
    -   Produced strict compliance matrix and risk assessment.
-   Human-in-the-loop governance:
    -   Final direction and acceptance decisions remained human-controlled.

## Failed Approaches

-   Treating task-page narrative filenames as canonical would risk parser mismatch; corrected by submitting schema-canonical YAML files first.
-   Assuming local replay completeness for patch regression checks from available assets was incorrect; local package contains metadata and patch diffs, not full runnable regression corpus.
-   Initial Task 3.3 prompt chunk files were summary placeholders; corrected by splitting the full master transcript into six evidence chunks.

## Efficiency Metrics

-   35/35 failures assigned exactly once across 5 buckets (no duplicates, no omissions).
-   5/5 patches mapped in `patch_validation.yaml` with required schema keys.
-   100% required Task 3.3 files present under `submission-3.3/`.
-   ZIP-first checks passed via:
    -   `manage-3.3-submissions.sh verify`
    -   `verify-3.3-readiness.sh --sim both`
    -   `verify-readiness.sh --tasks 3.3 --sim both --quick`
-   Prompt evidence packaged as 1 master transcript + 6 chunk files + prompts README in submission directory.

## Reproducibility

From repository root:

1. Activate environment:
    - `source .venv/bin/activate`
2. Regenerate prompt evidence (including Task 3.3 chunks):
    - `bash scripts/regenerate_prompt_evidence.sh`
3. Run structural validator directly:
    - `python submissions/task-3.3/submission-3.3/analysis_scripts/validate_task33.py --submission-dir submissions/task-3.3/submission-3.3 --failure-details phase3_materials/task_3_3_regression/failure_details.yaml --patches-dir phase3_materials/task_3_3_regression/patches`
4. Run package/extract/verify flow:
    - `bash scripts/manage-3.3-submissions.sh test-all`
5. Run ZIP-first readiness:
    - `bash scripts/verify-3.3-readiness.sh --sim both`

Note on evaluation confidence:

-   Current workspace assets support structure-complete submission and static patch mapping.
-   Empirical full-suite patch-regression replay requires runnable Task 3.3 regression corpus/log assets beyond the currently provided `phase3_materials/task_3_3_regression/` set.
