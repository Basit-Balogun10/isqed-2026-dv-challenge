# Task 2.3: Coverage-Directed Test Generation

## Agentic AI Design Verification Challenge 2026 -- Phase 2: Coverage Closure Campaign

| Property | Value |
|----------|-------|
| **Task ID** | 2.3 |
| **Phase** | 2 -- Coverage Closure Campaign |
| **Maximum Points** | 300 |
| **Per-DUT Scoring** | No (single system evaluated across DUTs) |
| **Difficulty** | 5 (most technically ambitious Phase 2 task) |
| **Estimated Effort** | 16--30 hours |
| **Evaluation Split** | Automated 80% / Judge 20% |

---

## Overview

Task 2.2 asks you to write tests that close coverage gaps. This task asks you to build a **system** that writes those tests for you -- and gets better at it over time.

Coverage-Directed Test Generation (CDG) is the frontier of verification automation. The idea is simple in principle and challenging in practice: after each simulation run, analyze which stimulus patterns produced useful coverage, then adjust your generation strategy to favor productive patterns and avoid wasteful ones.

This goes far beyond "generate tests and run them." A CDG system is an **adaptive feedback loop** where the AI observes coverage outcomes, reasons about what worked and what did not, and modifies its own generation behavior accordingly. The result should be measurably faster coverage convergence than static constrained-random testing.

---

## What You Must Build

### An AI-in-the-Loop CDG System

Your system must implement a closed-loop pipeline with the following stages:

```
  +-----------+     +-----------+     +------------+     +-------------+
  | Generate  | --> | Simulate  | --> | Collect    | --> | Analyze     |
  | Stimulus  |     |           |     | Coverage   |     | Results     |
  +-----------+     +-----------+     +------------+     +------+------+
       ^                                                        |
       |                                                        |
       +-------------------< Adjust Strategy >------------------+
```

**Stage 1: Generate Stimulus** -- Produce constrained-random or directed stimulus based on the current generation strategy (constraint weights, enabled scenarios, randomization distributions).

**Stage 2: Simulate** -- Run the generated stimulus on the DUT using Verilator or Icarus Verilog. Collect simulation results.

**Stage 3: Collect Coverage** -- Extract line, branch, toggle, FSM, and functional coverage metrics from the simulation run.

**Stage 4: Analyze Results** -- Compare the new coverage against previous runs. Determine which stimulus patterns contributed new coverage and which were redundant.

**Stage 5: Adjust Strategy** -- Modify the generation parameters for the next iteration. This is where the AI reasoning happens. The system must decide: which constraint ranges to widen or narrow, which scenarios to prioritize, which generation patterns to retire, and which new patterns to try.

### Requirements

1. **Closed-loop operation.** The system must run autonomously for at least 10 iterations without human intervention. Each iteration consists of generate, simulate, collect, analyze, and adjust.

2. **Observable adaptation.** The system must produce logs showing how its generation strategy changes across iterations. Judges must be able to trace the reasoning: "Iteration 3 coverage report showed branch X uncovered; iteration 4 added constraint Y; iteration 5 covered branch X."

3. **Measurable improvement.** The system must achieve higher coverage per simulation cycle than the baseline (static constrained-random with fixed distributions). This is measured as the area under the coverage-vs-cycles curve.

4. **DUT-agnostic framework.** While the system will be evaluated on specific DUTs, its architecture should be parameterizable -- able to accept a new DUT with appropriate configuration rather than being hardcoded to one design.

---

## Evaluation Scenarios

Your CDG system will be evaluated on three metrics, each measured against a baseline of static constrained-random testing with the same cycle budget:

### Metric 1: Coverage Efficiency (coverage per cycle)

The system runs for a fixed cycle budget and coverage is sampled at regular intervals. The resulting coverage-vs-cycles curve is compared against the baseline curve. A system that reaches the same coverage in fewer cycles scores higher.

### Metric 2: Convergence Rate to 85%

How many simulation cycles does the system need to reach 85% combined coverage (averaged across line, branch, and functional)? The baseline typically requires the full 100k cycle budget and may not reach 85%. Systems that converge faster score higher. Systems that converge to a higher ceiling also receive credit.

### Metric 3: Total Coverage at 100k Cycles

After 100,000 simulation cycles, what is the total coverage achieved? This is the simplest metric -- pure coverage at the end of the budget. It rewards systems that continue finding productive stimulus even as coverage plateaus.

---

## Technical Approaches

There are several valid architectures for a CDG system. Your approach does not need to use all of these, but here are the techniques that the task is designed to evaluate:

### Approach A: LLM-Guided Constraint Tuning

Use an LLM to analyze uncovered RTL regions and generate updated constraint distributions. The LLM receives the coverage report and the current constraint definitions, then produces modified constraints that bias stimulus toward uncovered regions.

### Approach B: Reinforcement-Style Feedback

Treat each constraint parameter as a lever. After each simulation run, score the run's coverage contribution. Increase the probability of parameter settings that produced new coverage; decrease the probability of settings that contributed nothing.

### Approach C: Coverage-Point Targeting

Maintain a priority queue of uncovered coverage points. For each iteration, select the highest-priority uncovered point and generate stimulus specifically designed to reach it. Remove points from the queue as they are covered.

### Approach D: Hybrid Approaches

Combine LLM reasoning with algorithmic optimization. For example, use the LLM to identify *which* coverage gaps to target, then use a search algorithm to find the specific constraint values that reach those gaps.

---

## Inputs Provided

| Material | Format | Description |
|----------|--------|-------------|
| RTL source | SystemVerilog | Full DUT source for evaluation DUTs |
| Reference testbench | Python (cocotb) | Baseline environment with agents, scoreboard, and basic sequences |
| Baseline coverage data | `.dat` + JSON | Coverage from static constrained-random baseline (100k cycles) |
| Constraint templates | Python | Parameterizable constraint definitions for each DUT |
| CDG harness | Python | A harness that manages the simulate-collect loop; your system plugs into the `generate()` and `adjust()` hooks |

### CDG Harness Interface

Your system must implement two functions that the evaluation harness calls:

```python
class CDGSystem:
    def generate(self, iteration: int, coverage_state: CoverageState) -> Stimulus:
        """
        Produce stimulus for the next simulation run.

        Args:
            iteration: Current iteration number (0-indexed)
            coverage_state: Coverage data from all previous iterations

        Returns:
            Stimulus object containing constraint parameters and
            directed sequences for this iteration
        """
        ...

    def adjust(self, iteration: int, new_coverage: CoverageReport,
               cumulative_coverage: CoverageState) -> None:
        """
        Update internal strategy based on latest results.

        Args:
            iteration: Iteration that just completed
            new_coverage: Coverage delta from this iteration only
            cumulative_coverage: Total accumulated coverage
        """
        ...
```

---

## Submission Format

```
submission-2.3/
├── cdg_system/
│   ├── cdg.py                 -- Main CDG system (implements CDGSystem interface)
│   ├── strategy.py            -- Strategy/policy logic
│   ├── analyzer.py            -- Coverage analysis and gap identification
│   ├── generator.py           -- Stimulus generation from strategy
│   └── config.yaml            -- System configuration and parameters
├── logs/
│   ├── iteration_log.yaml     -- Per-iteration decisions and outcomes
│   ├── strategy_evolution.yaml -- How strategy changed over time
│   └── coverage_curve.csv     -- Coverage vs. cycle data
├── results/
│   ├── final_coverage.html    -- Final coverage report
│   ├── convergence_plot.png   -- Coverage-vs-cycles visualization (optional)
│   └── baseline_comparison.md -- Analysis of CDG vs. baseline performance
├── methodology.md             -- Architecture rationale, AI integration details
└── metadata.yaml              -- Team info, task ID
```

---

## Evaluation Rubric

### Automated Evaluation (80% -- 240 pts)

The automated evaluator runs your CDG system through the harness on one or more DUTs and measures coverage outcomes.

| Criterion | Points | Method |
|-----------|--------|--------|
| **Coverage efficiency** | 80 | Area under coverage-vs-cycles curve, normalized against baseline. Ratio > 1.0 (better than baseline) earns points proportionally. A system with 2x the baseline efficiency earns full points. |
| **Convergence rate to 85%** | 80 | Cycles needed to reach 85% combined coverage. Baseline budget is 100k cycles. Systems reaching 85% in fewer than 50k cycles earn full points. Systems that never reach 85% receive partial credit based on their ceiling. |
| **Total coverage at 100k cycles** | 80 | Absolute coverage at the end of the fixed budget. Baseline achieves roughly 60% combined. Each percentage point above baseline earns 2 pts, up to 80 pts. |

**Technical Requirements (must pass to receive any automated points):**

- System must implement the `CDGSystem` interface correctly
- System must run for at least 10 iterations without crashing
- System must complete within a 30-minute wall-clock timeout
- System must not modify the RTL or the evaluation harness

### Judge Evaluation (20% -- 60 pts)

| Criterion | Points | What Judges Look For |
|-----------|--------|----------------------|
| **CDG architecture innovation** | 30 | Novelty and sophistication of the adaptive strategy. Is the system genuinely learning from feedback, or is it following a fixed script? Does it combine multiple techniques effectively? |
| **Observability and explainability** | 15 | Can judges understand *why* the system made each decision? Are the iteration logs clear? Can the strategy evolution be traced from start to finish? |
| **Generalizability** | 15 | Could this system work on a new, unseen DUT with reasonable configuration effort? Is the architecture DUT-agnostic, or is it hardcoded to specific designs? |

### Scoring Summary

| Component | Weight | Max Points |
|-----------|--------|------------|
| Automated: Coverage efficiency | -- | 80 |
| Automated: Convergence rate | -- | 80 |
| Automated: Total coverage at 100k | -- | 80 |
| Judge: Architecture innovation | -- | 30 |
| Judge: Observability | -- | 15 |
| Judge: Generalizability | -- | 15 |
| **Total** | **100%** | **300** |

---

*Agentic AI Design Verification Challenge 2026 -- ISQED 2026*
