# 04 — Task 4.3 Generation Quality Prompt

## Prompt Intent

Maximize judge-facing quality for vplan, coverage model, assertions, and test
stubs while avoiding hallucinated features.

## Prompt Snapshot

- Prioritize feature completeness and risk-aware ordering.
- Include purposeful coverage crosses only where operationally meaningful.
- Emphasize safety + liveness assertion mix with temporal behavior language.
- Generate test stubs that clearly define setup, stimulus, checks, and expected
  outcome with implementation-time helper placeholders.

## Outcome

- Improved non-triviality and readability of generated artifacts.
- Reduced risk of irrelevant or fabricated feature generation.
