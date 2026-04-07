# Methodology

This document records the actual Task 2.3 execution history for
submission-2.3 under Path A.

Task context:

-   Task: 2.3 (Coverage-Directed Test Generation)
-   DUT: sentinel_hmac
-   CDG strategy: hybrid Approach B + C (reinforcement-style policy updates + coverage-point targeting)
-   Autonomous iterations: 12
-   Budget run used for final artifacts: 100000 cycles (results show 99996 used)
-   Final combined coverage (line+branch+functional)/3: 75.98
-   Adaptive-vs-baseline efficiency ratio (AUC): 1.0540

Master transcript source for prompt evidence:

-   Repository path: submissions/task-2.3/prompts.md
-   GitHub URL: https://github.com/Basit-Balogun10/isqed-2026-dv-challenge/blob/main/submissions/task-2.3/prompts.md

## AI Tools Used

-   GitHub Copilot (GPT-5.3-Codex) for CDG architecture, implementation, debugging, packaging, and readiness automation.
-   Local open-source simulation toolchain (Icarus + Verilator + cocotb + verilator_coverage) for execution and coverage extraction.
-   Workspace shell automation for ZIP-first verification and submission integrity checks.
-   No external runtime LLM API dependency for Task 2.3 execution.

## Prompt Engineering Strategies

-   Requirement-anchored prompting: every code change was tied directly to Task 2.3 task text and submission-requirements gates.
-   Scoring-oriented prompting: prioritized coverage efficiency and convergence behavior over static random volume.
-   Observability-first prompting: required explicit per-iteration logs with policy-after snapshots and strategy-evolution traceability.
-   Compatibility prompting: implemented both naming families from documentation (cdg_engine.py and cdg.py/analyzer.py/strategy.py/generator.py) to reduce checker mismatch risk.
-   Packaging-evidence prompting: enforced prompt chunking, prompt README source linkage, and readiness checks against extracted ZIP payloads.

## Iteration Process

1. Audit and planning

-   Audited Task 2.3 requirements and rubric constraints, including closed-loop behavior, adaptation evidence, and 100k-cycle command compatibility.
-   Chose sentinel_hmac as the demonstration DUT based on existing stable Task 2.2 infrastructure.

2. CDG system implementation

-   Implemented core CDG modules:
    -   cdg_system/cdg.py (CDGSystem with generate() and adjust())
    -   cdg_system/generator.py (stimulus generation with knob policies)
    -   cdg_system/coverage_analyzer.py (line/branch/toggle/functional parsing)
    -   cdg_system/constraint_tuner.py (reward-driven policy updates)
    -   cdg_system/cdg_engine.py (orchestration CLI and iteration loop)
-   Added compatibility shim modules (analyzer.py and strategy.py) for doc-variant naming expectations.

3. Runtime and observability hardening

-   Integrated deterministic JSON stimulus handoff into tests/test_cdg_generated.py.
-   Enforced target cycle consumption in generated tests.
-   Added required and judge-facing artifacts:
    -   results/convergence_log.csv
    -   results/final_coverage.txt
    -   logs/iteration_log.yaml
    -   logs/strategy_evolution.yaml
    -   logs/coverage_curve.csv
-   Added static baseline run and AUC comparison report (results/baseline_comparison.md).

4. Packaging and verification automation

-   Implemented scripts/manage-2.3-submissions.sh and scripts/verify-2.3-readiness.sh.
-   Integrated Task 2.3 into scripts/verify-readiness.sh and scripts/README.md.
-   Added prompt-evidence generation support in scripts/regenerate_prompt_evidence.sh.

5. Final validation and audit pass

-   Executed required 100k command and regenerated final artifacts.
-   Rebuilt ZIP and validated structure, prompt evidence presence, dual-simulator compile smoke, and forbidden artifact policy checks.

## Human vs AI Contribution

-   Human-led: acceptance criteria, execution direction, and final signoff gates.
-   AI-led: CDG module implementation, generated test integration, script automation, and multi-pass compliance hardening.
-   Joint: strategy selection (self-contained hybrid B+C), adaptation trace interpretation, and final packaging policy decisions.

## Failed Approaches

-   Runtime external LLM API control loop was rejected because it introduces nondeterministic dependency and infrastructure risk for evaluation.
-   Pure static random policy was rejected because it cannot satisfy adaptation intent or maximize innovation/explainability scoring.
-   Initial convergence output format was hardened to strict required CSV header after audit detection.
-   YAML alias-heavy logs were replaced with alias-free dumps for clearer per-iteration judge traceability.

## Efficiency Metrics

-   Autonomous iterations: 12 (minimum required >=10).
-   Final budget run: 100000 requested, 99996 accounted in results.
-   Final coverage snapshot:
    -   line: 51.53
    -   branch: 76.43
    -   toggle: 52.98
    -   functional: 100.00
    -   combined: 75.98
-   Adaptive-vs-baseline comparison:
    -   adaptive AUC: 6981359.62
    -   baseline AUC: 6623373.94
    -   efficiency ratio: 1.0540
-   Readiness outcome: quick/full Task 2.3 verification green with dual-simulator compile checks.

## Reproducibility

Environment:

-   Path A (cocotb + open-source simulators)
-   Python virtual environment at .venv

Core commands:

1. source .venv/bin/activate
2. cd submissions/task-2.3/submission-2.3
3. make SIM=icarus compile DUT_PATH=../../../duts
4. make SIM=verilator compile DUT_PATH=../../../duts
5. python cdg_system/cdg_engine.py --dut sentinel_hmac --budget 100000 --output results/
6. cd ../../..
7. bash scripts/manage-2.3-submissions.sh test-all
8. bash scripts/verify-2.3-readiness.sh --sim both

Evidence set:

-   prompts/README.md + six prompt chunk files
-   logs/iteration_log.yaml
-   logs/strategy_evolution.yaml
-   logs/coverage_curve.csv
-   logs/baseline_curve.csv
-   results/baseline_comparison.md
