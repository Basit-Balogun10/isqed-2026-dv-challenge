# Methodology

This document records the actual Task 4.1 execution flow for submission-4.1 under Path A, including implementation, compliance audits, and packaging hardening.

Master prompt transcript source:

- Repository path: submissions/task-4.1/prompts.md
- GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-4.1/prompts.md

## AI Tools Used

- GitHub Copilot Chat (GPT-5.3-Codex) for architecture, implementation, and compliance hardening.
- OpenAI API integration through `OPENAI_API_KEY`, with staged model usage (`gpt-5.4-mini` first, escalation to `gpt-5.4` for judge-threshold misses).
- Python automation for RTL/spec/CSR parsing, cocotb environment generation, simulation execution, coverage parsing, and submission validation.

## Prompt Engineering Strategies

- Requirement-first prompting: all implementation choices were anchored to Task 4.1 requirements, submission schema, and scoring rubric clauses before coding.
- Score-aware prompting: prompts prioritized compile stability, transaction-scoreboard correctness, and low false-positive behavior before pushing additional coverage.
- Failure-context prompting: iterative repair prompts include simulator errors, failing test modules, and extracted RTL context to drive targeted rewrites.
- Two-tier model prompting: baseline generation on `gpt-5.4-mini`, then escalation prompts on `gpt-5.4` when convergence plateaus or quality gates remain unmet.

## Iteration Process

1. Audited Task 4.1 requirements against all governing documents.
2. Resolved document ambiguities by using submission schema as parser-canonical while retaining compatibility behaviors.
3. Implemented staged orchestrator pipeline (analyze, plan, build, test, measure, iterate, report).
4. Added escalation loop (gpt-5.4-mini xhigh first, then gpt-5.4 xhigh on judge-threshold miss).
5. Replaced generic scenario loops with requirement-tagged semantic cocotb tests for both directed and random lanes.
6. Added failure-context repair loop: on iteration failures, pass simulator errors + failing test code + RTL context back to the LLM and rewrite failing test modules.
7. Added full-regression guard on every iteration update so each repair/risk test reruns directed and random suites to detect regressions immediately.
8. Added plateau escalation: when consecutive iterations are near-flat and still below target or failing, generate a stronger escalation test with the larger model.
9. Added auto-iteration growth with hard cap and timeout-aware graceful stop reporting.
10. Ran clause-by-clause compliance audits and fixed identified gaps (readiness gate alignment and timeout default alignment).
11. Rebuilt prompt evidence to match prior task packaging style by splitting the full Task 4.1 transcript into six indexed chunks.
12. Revalidated local readiness in no-spend mode and rebuilt submission packaging.

## Human vs AI Contribution

- Human: set strategic direction, risk posture, and acceptance criteria.
- AI: produced implementation and validation automation.
- Human-in-the-loop: reviewed architecture decisions and enforced compliance quality gates.

## Failed Approaches

- Pure template-only generation was too brittle for unseen DUT variation.
- Overly permissive bug reporting increased false-positive risk and was constrained.
- Generic traffic-loop wrappers for plan scenarios were insufficiently requirement-specific and were replaced with semantic scenario logic.
- Initial prompt evidence packaging with five representative files did not match the full-transcript chunk style used in prior tasks and was replaced.
- A readiness gate that hard-required `.env.example` introduced unnecessary friction and was removed.
- A `timeout_minutes=0` default could disable practical budget locking and was corrected to default to 60 minutes.

## Efficiency Metrics

- Agent pipeline implemented with bounded stage budgets.
- LLM call accounting captured in agent_log metadata/actions.
- Automatic model escalation triggers only when quality threshold is unmet.
- Iteration logging captures mode, extension events, and stop reasons for traceability.

## Reproducibility

- Entry command: `python agent/run_agent.py --rtl <path> --spec <path> --csr_map <path> --output_dir <path> --simulator <auto|icarus|verilator|both> --max_iterations <1..12> --max_repair_generations_per_iteration <0..N> --iteration_mode <fixed|auto> --min_iterations <1..12> --auto_extension_step <>=1> --timeout_minutes <>=0>`.
- Makefile helper: `make run_agent RTL=<rtl_dir_or_file> SPEC=<spec_md> CSR_MAP=<csr_hjson> output_dir=<out_dir> SIMULATOR=<auto|icarus|verilator|both> MAX_ITERATIONS=<1..12> ITERATION_MODE=<fixed|auto> MIN_ITERATIONS=<1..12> AUTO_EXTENSION_STEP=<>=1> TIMEOUT_MINUTES=<>=0`.
- No-spend readiness path: `NO_API_SPEND=1 ./scripts/verify-4.1-readiness.sh`.
- Agent log captures actions, timing, and LLM call summaries in `agent_log.json`.
- Iteration state is captured in `iteration_log.json` with extension and stop-reason metadata.

### Evaluator Setup Requirements

**Evaluation uses online OpenAI calls for Task 4.1 generation. Provide a valid `OPENAI_API_KEY` in the evaluator environment before launching `run_agent.py`.**

#### Environment Setup

1. Create and activate a virtual environment:
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
2. Install dependencies:
    - `pip install -r agent/requirements.txt`

#### API Key Setup

1. Export key in shell:
    - `export OPENAI_API_KEY=sk-proj-...`
2. Confirm key availability before running:
    - `python -c "import os; print(bool(os.getenv('OPENAI_API_KEY')))"`

#### Common Runtime Fixes

- `ModuleNotFoundError: No module named 'openai'`:
  - Ensure virtual environment is active and reinstall requirements.
- `ModuleNotFoundError` for `yaml` or `hjson`:
  - Run `pip install -r agent/requirements.txt`.
- `OPENAI_API_KEY is required for Task 4.1 online mode`:
  - Export `OPENAI_API_KEY` in the execution shell before launching the agent.