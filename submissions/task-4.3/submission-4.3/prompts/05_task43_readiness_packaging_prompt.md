# 05 — Task 4.3 Readiness and Packaging Prompt

## Prompt Intent

Define repeatable readiness checks for structure, syntax, optional API-backed
smoke run, and canonical zip payload verification.

## Prompt Snapshot

- Validate required submission files and Makefile targets.
- Validate CLI arguments from `--help` output.
- In no-spend mode, skip API-backed run while still validating parser surfaces.
- When enabled, run a sample spec and validate generated YAML/Python artifacts.
- Package canonical archive at `submissions/zips-4.3/submission-4.3.zip` and
  verify prompt evidence files exist in zip payload.

## Outcome

- Added deterministic local quality gate via `scripts/verify-4.3-readiness.sh`.
- Reduced risk of stale or incomplete packaged submissions.
