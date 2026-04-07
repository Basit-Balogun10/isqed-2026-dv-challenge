# Methodology

This document records the Task 4.2 implementation and hardening process for
submission-4.2 under Path A.

Master prompt transcript source:

- Repository path: submissions/task-4.2/prompts.md
- GitHub URL: [Task 4.2 master prompts](https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-4.2/prompts.md)

## AI Tools Used

1. GitHub Copilot Chat (GPT-5.3-Codex) for requirements audit, architecture
    design, implementation, debugging, and compliance hardening.
1. OpenAI API integration through `OPENAI_API_KEY` for commit-level verdict
    reasoning in Task 4.2 stream analysis.
1. Model policy fixed to `gpt-5.4-mini` with `xhigh` reasoning effort and no
    escalation path.

## Prompt Engineering Strategies

1. Schema-first prompting: constrained model outputs to strict JSON verdict
    payloads that map to evaluator-required fields.
1. Diff-grounded prompting: supplied unified diff, files changed, selected test
    subset, and linked bug-ledger context per commit.
1. Penalty-aware prompting: tuned decision posture to avoid false negatives
    first, then reduce false positives.
1. Structured repair prompting: when model output was not strict JSON, issued a
    one-pass JSON repair prompt to preserve deterministic parsing.

## Iteration Process

1. Audited Task 4.2 requirements across task spec, submission requirements,
    rubric, and competition rules.
1. Resolved contract mismatch by treating submission requirements as
    parser-canonical, while adding compatibility files for task-page entrypoint
    expectations.
1. Reused Task 4.1 primitives (logger/provider/utils) and replaced the core
    orchestrator with commit-stream workflow.
1. Implemented runtime initialization, commit processing, and finalize stages
    with persistent open/closed bug ledger.
1. Added impact analysis (changed-module inference), risk classification,
    bounded targeted test selection, and linked-bug test augmentation.
1. Added coverage-delta quantification and threshold-based
    `COVERAGE_REGRESSION` handling.
1. Added run-progress telemetry (`run_progress.json`) plus stream-level summary
    artifacts.
1. Implemented monitored execution helper and hardened no-run mode completion
    fallback using `stream_summary.json` + `agent_log.json`.
1. Added Task 4.2 readiness automation with no-spend mode and zip inclusion
    checks for prompt evidence.
1. Added submission compatibility shims (`run_regression_agent.py` and root
    `requirements.txt`) to satisfy both document dialects.
1. Repackaged prompt evidence from the full Task 4.2 master transcript into
    indexed chunk files.

## Human vs AI Contribution

1. Human: set strategy, constraints, and final acceptance criteria.
1. AI: implemented orchestration logic, telemetry, readiness scripts,
    compatibility wrappers, and documentation.
1. Human-in-the-loop: reviewed compliance decisions, model policy lock
    (`gpt-5.4-mini` + `xhigh`), and packaging scope.

## Failed Approaches

1. Treating task-page entrypoint as parser-canonical was rejected; submission
    schema CLI was treated as authoritative for evaluator compatibility.
1. Initial monitor no-run flow that depended only on `run_progress.json` was
    rejected because completed historical runs may only have
    `stream_summary.json`.
1. Per-commit full-suite testing was rejected due runtime cost and speed-bonus
    risk.
1. Generic prompt placeholders were replaced with transcript-grounded evidence
    chunks sourced from the full Task 4.2 prompt log.

## Efficiency Metrics

1. Per-commit pipeline is bounded and records decision time.
1. LLM accounting is captured in `agent_log.json` metadata and
    `llm_api_calls`, including token counts and estimated USD cost.
1. Runtime summary includes average seconds per commit and average calls/tokens
    per commit.
1. Test scope is reduced with changed-module and risk heuristics plus
    bug-ledger-linked augmentation.
1. Latest API-backed readiness dry run (2026-04-07 UTC) processed 20 commits
    with 17 LLM calls, 70,385 total tokens, and estimated cost of $0.120818.

## Reproducibility

From repository root:

1. Activate environment:
    - `source .venv/bin/activate`
2. Install dependencies:
    - `pip install -r submissions/task-4.2/submission-4.2/agent/requirements.txt`
3. Export key:
    - `export OPENAI_API_KEY=sk-proj-...`
4. Preferred live mode (HTTP):
    - `python submissions/task-4.2/submission-4.2/run_regression_agent.py --baseline_rtl duts/nexus_uart --baseline_env skeleton_envs/nexus_uart --output_dir submissions/task-4.2/submission-4.2/output_http`
5. Canonical evaluator mode (file stream):
    - `python submissions/task-4.2/submission-4.2/agent/run_agent.py --commit_stream submissions/task-4.2/submission-4.2/sample_commit_stream.json --rtl_base duts/nexus_uart --test_suite skeleton_envs/nexus_uart --output_dir submissions/task-4.2/submission-4.2/output_eval`
6. Readiness without API spend:
    - `NO_API_SPEND=1 ./scripts/verify-4.2-readiness.sh`
7. Readiness with API-backed dry run:
    - `NO_API_SPEND=0 ./scripts/verify-4.2-readiness.sh --keep-workdir`

### Evaluator Setup Requirements

1. Provide `OPENAI_API_KEY` in evaluator environment.
1. Use Python 3.11+ and install `agent/requirements.txt`.
1. Launch from submission root or repository root with valid baseline RTL/test
   suite paths.
1. Avoid storing API keys in repository files, zip archives, or logs.
