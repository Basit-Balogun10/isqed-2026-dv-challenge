# 03 — Task 4.3 Orchestrator Design Prompt

## Prompt Intent

Design a robust orchestration pipeline for spec-only interpretation that can run
with LLM assistance while remaining resilient to malformed outputs.

## Prompt Snapshot

- Build heuristic baseline from markdown headings and requirement keywords.
- Call LLM with strict JSON schema and bounded output sizes.
- Sanitize model output: normalize priorities/risks, bound list lengths,
  enforce IDs, and ensure non-empty test/assertion links.
- Fallback to heuristic output when API call fails or parsing fails.

## Outcome

- Added deterministic fallback and sanitization gates.
- Ensured artifact generation is never blocked by model formatting issues.
