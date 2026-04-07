# Methodology

This document records the Task 4.3 implementation and hardening process for
submission-4.3 under Path A.

Master prompt transcript source:

- Repository path: submissions/task-4.3/submission-4.3/prompts/
- GitHub URL: [Task 4.3 prompt evidence](https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/tree/main/submissions/task-4.3/submission-4.3/prompts)

## AI Tools Used

1. GitHub Copilot Chat (GPT-5.3-Codex) for requirements audit, architecture
design, implementation, debugging, and compliance hardening.
1. OpenAI API integration through `OPENAI_API_KEY` for specification
interpretation and artifact synthesis.
1. Model policy fixed to `gpt-5.4-mini` with `xhigh` reasoning effort and no
escalation path.

## Prompt Engineering Strategies

1. Schema-first prompting: constrained model outputs to strict JSON that maps
   directly to Task 4.3 deliverables.
1. Hallucination control: injected a heuristic baseline interpretation and
   enforced conservative normalization of model outputs.
1. Repair prompting: when model output is non-JSON, issue a single strict JSON
   repair pass to preserve deterministic parsing.
1. Dual-layout output prompting: preserve canonical submission schema while
   mirroring optional task-page directory layout.

## Iteration Process

1. Audited Task 4.3 requirements across task spec, submission requirements,
   rubric, and competition rules.
1. Resolved contract mismatch by treating submission requirements as
   parser-canonical, with compatibility wrapper for task-page entrypoint.
1. Reused Task 4.2 primitives (`agent_logger.py`, `llm_provider.py`,
   `io_utils.py`) and implemented a new spec interpretation orchestrator.
1. Implemented heuristic-first interpretation and LLM-assisted enrichment with
   strict post-sanitization.
1. Added generation of all required artifacts: verification plan, cocotb stubs,
   coverage model, assertions, report, and structured `agent_log.json`.
1. Added compatibility mirror outputs (`tests/`, `coverage/`, `assertions/`)
   to reduce evaluator dialect risk.
1. Added readiness automation, zip-path canonicalization, and no-spend validation
   mode for local quality gates.

## Human vs AI Contribution

1. Human: set strategic constraints (model lock, no escalation, cost-aware run
   policy, schema-canonical packaging).
1. AI: implemented orchestrator, generation pipeline, wrappers, readiness
   scripts, and submission documentation.
1. Human-in-the-loop: approved contract reconciliation and packaging decisions.

## Failed Approaches

1. Treating task-page output structure as canonical was rejected because
   submission schema defines evaluator-required top-level output files.
1. Generating unbounded feature/covergroup/assertion counts was rejected due
   quality dilution risk under judge review.
1. Relying on model-only interpretation was rejected; heuristic fallback and
   sanitization were added to improve robustness.

## Efficiency Metrics

1. LLM accounting is captured in `agent_log.json` metadata and `llm_api_calls`.
1. Estimated API spend is computed from prompt/completion token pricing in
   `agent/agent_config.yaml`.
1. Artifact counts (features/tests/covergroups/assertions) are bounded and
   configurable for predictable runtime.

## Reproducibility

From repository root:

1. Activate environment:
   - `source .venv/bin/activate`
1. Install dependencies:
   - `pip install -r submissions/task-4.3/submission-4.3/agent/requirements.txt`
1. Export key:
   - `export OPENAI_API_KEY=sk-proj-...`
1. Run canonical entrypoint:
   - `python submissions/task-4.3/submission-4.3/agent/run_agent.py --spec submissions/task-4.3/submission-4.3/sample_spec.md --output_dir submissions/task-4.3/submission-4.3/output_eval`
1. Compatibility wrapper:
   - `python submissions/task-4.3/submission-4.3/run_spec_interpreter.py --spec submissions/task-4.3/submission-4.3/sample_spec.md --output_dir submissions/task-4.3/submission-4.3/output_eval`
1. Readiness without API spend:
   - `NO_API_SPEND=1 ./scripts/verify-4.3-readiness.sh`
1. Readiness with API-backed dry run:
   - `NO_API_SPEND=0 ./scripts/verify-4.3-readiness.sh --keep-workdir`

### Evaluator Setup Requirements

1. Provide `OPENAI_API_KEY` in evaluator environment.
1. Use Python 3.11+ and install `agent/requirements.txt`.
1. Launch from submission root or repository root with a valid markdown spec path.
1. Avoid storing API keys in repository files, zip archives, or logs.
