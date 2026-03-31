# Task 2.1: Coverage Gap Analysis

## Agentic AI Design Verification Challenge 2026 -- Phase 2: Coverage Closure Campaign

| Property | Value |
|----------|-------|
| **Task ID** | 2.1 |
| **Phase** | 2 -- Coverage Closure Campaign |
| **Maximum Points** | 200 |
| **Per-DUT Scoring** | No (single submission across all DUTs) |
| **Difficulty** | 3 |
| **Estimated Effort** | 4--8 hours |
| **Evaluation Split** | Automated 30% / Judge 70% |

---

## Overview

Your testbenches run. Coverage numbers come back. Line coverage is at 42%, branch coverage at 31%, functional coverage at 18%. The question every verification engineer faces next is: **where are the gaps, and what stimulus would close them?**

In this task, you will analyze the reference testbench coverage database and produce a structured, prioritized gap analysis. This is the strategic planning step that precedes the stimulus engineering work in Task 2.2 -- get it right here, and coverage closure becomes a targeted campaign rather than a blind search.

---

## Inputs Provided

You will receive the following materials for each DUT in the competition:

| Material | Format | Description |
|----------|--------|-------------|
| Verilator coverage database | `.dat` file | Raw coverage data from the reference testbench run |
| Annotated coverage report | HTML + annotated source | Line-by-line coverage annotations on RTL source |
| Functional coverage report | JSON | Covergroup/coverpoint/cross bin hit counts from cocotb-coverage |
| Reference testbench source | Python (cocotb) | The testbench that produced these coverage numbers |
| RTL source | SystemVerilog | Full DUT source under `duts/<dut_name>/` |
| Specification | Markdown | DUT specification document |
| Verification plan | YAML | Structured vplan with features, scenarios, and coverage bins |

### Coverage Types in the Database

- **Line coverage**: Which RTL source lines were executed during simulation
- **Branch coverage**: Which conditional branches (if/else, case arms) were taken
- **Toggle coverage**: Which signals transitioned both 0-to-1 and 1-to-0
- **FSM coverage**: Which FSM states were visited, which transitions were taken
- **Functional coverage**: Which user-defined coverpoints, bins, and crosses were hit

---

## What You Must Produce

### 1. Structured Gap Analysis Report (`gap_analysis.yaml`)

A YAML-formatted report identifying every significant coverage gap. For each gap, provide:

```yaml
gaps:
  - id: "GAP-001"
    dut: "nexus_uart"
    coverage_type: "branch"        # line | branch | toggle | fsm_state | fsm_transition | functional
    location:
      file: "nexus_uart_tx.sv"
      line_range: "142-158"
      module: "nexus_uart_tx"
      block: "parity_generation"
    metric:
      current_coverage: 0.25       # 25% of branches in this block covered
      target_coverage: 0.85
      uncovered_items: 6           # number of uncovered branches/lines/bins
    severity: "high"               # critical | high | medium | low
    difficulty: "medium"           # easy | medium | hard | very_hard
    root_cause: >
      The reference testbench only exercises even parity mode. Odd parity,
      no-parity, and mark/space parity configurations are never tested,
      leaving all branches in the parity selection logic uncovered.
    test_intent: >
      Generate UART transmissions with each parity mode (none, even, odd,
      mark, space) and verify correct parity bit insertion across multiple
      data patterns including all-zeros, all-ones, and alternating bits.
    recommended_stimulus:
      - "Configure CTRL.PARITY to each valid mode"
      - "Transmit at least 4 frames per mode with varying data"
      - "Include error injection: wrong parity on RX path"
    dependencies:
      - "Requires parity checker in monitor to validate"
    vplan_items:
      - "uart.tx.parity.all_modes"
      - "uart.tx.parity.error_detection"
```

### 2. Gap Summary Table (`gap_summary.md`)

A human-readable markdown summary that provides:

- **Per-DUT coverage snapshot**: current vs. target for each coverage type
- **Top 10 gaps by severity**: the most impactful uncovered regions
- **Coverage heat map**: which RTL modules have the worst coverage and why
- **Effort estimation**: rough ordering of gaps from quick-wins to hard problems

### 3. Prioritized Closure Plan (`closure_plan.md`)

A recommended order of attack for closing gaps, organized as:

- **Quick wins** (gaps that can likely be closed with simple stimulus changes)
- **Moderate effort** (gaps requiring new sequences or constraint modifications)
- **Hard targets** (gaps requiring architectural understanding, corner-case reasoning, or new infrastructure)
- **Dependencies** between gaps (e.g., "closing GAP-003 requires the monitor built for GAP-001")

---

## Analysis Requirements

### Completeness

Your analysis must cover **all DUTs** in the competition materials. You are not required to analyze every single uncovered line, but you must identify and categorize the **major coverage gaps** -- defined as any region where coverage falls below 50% and the gap affects more than 5 lines or 3 branches.

### Root Cause Depth

For each gap, the root cause must explain **why** the reference testbench fails to cover this region. Acceptable root causes include:

- Missing stimulus configuration (e.g., a mode never enabled)
- Missing protocol sequence (e.g., a transaction type never issued)
- Missing error injection (e.g., error paths never exercised)
- Insufficient randomization range (e.g., constraints too narrow)
- Missing temporal scenario (e.g., back-to-back transactions never tested)
- Infrastructure limitation (e.g., no monitor for a specific interface)

Unacceptable root causes: "This line is not covered" (that is the symptom, not the cause).

### Test Intent Clarity

Each gap's `test_intent` field must describe the verification goal in plain language. A verification engineer reading only the test intent should understand exactly what test to write, without needing to look at the RTL or coverage data.

---

## Why This Task Tests AI Capabilities

Coverage gap analysis is a task where AI can provide significant leverage:

- **Pattern recognition**: LLMs can scan annotated RTL source and identify clusters of uncovered code that share a common root cause (e.g., an entire error-handling path that is never exercised).
- **Specification cross-referencing**: AI can correlate uncovered RTL regions with specification requirements to determine which features are untested.
- **Natural-language reasoning**: Producing clear test intents and root cause descriptions requires understanding the design's purpose, not just its structure.

However, the challenge lies in **noise filtering**. Coverage databases are large, and not all uncovered regions are equally important. Toggle coverage on clock-gating signals, for example, may be architecturally unreachable. The quality of your analysis depends on distinguishing real gaps from noise.

---

## Submission Format

```
submission-2.1/
├── gap_analysis.yaml          -- Structured gap data (required)
├── gap_summary.md             -- Human-readable summary (required)
├── closure_plan.md            -- Prioritized closure strategy (required)
├── methodology.md             -- AI tools and process documentation (required)
└── metadata.yaml              -- Team info and task ID
```

---

## Evaluation Rubric

### Automated Evaluation (30% -- 60 pts)

The automated evaluator compares your identified gaps against the ground-truth coverage database.

| Criterion | Points | Method |
|-----------|--------|--------|
| **Gap identification accuracy** | 40 | Each gap in `gap_analysis.yaml` is checked against the actual coverage DB. Correctly identified uncovered regions earn points; fabricated gaps (regions that are actually covered) incur a penalty of -5 pts each. |
| **Coverage type correctness** | 10 | The `coverage_type` field must match the actual type of gap (e.g., do not label a branch gap as a line gap). |
| **Structural validity** | 10 | The YAML file must parse correctly, all required fields must be present, and file/line references must point to real locations in the RTL source. |

### Judge Evaluation (70% -- 140 pts)

A panel of verification experts reviews the quality of your analysis.

| Criterion | Points | What Judges Look For |
|-----------|--------|----------------------|
| **Completeness** | 100 | Does the analysis cover all major gaps across all DUTs? Are there significant uncovered regions that the analysis missed entirely? Judges compare against a reference gap list. |
| **Root cause accuracy** | 50 | Are the root causes correct and specific? Does each root cause explain *why* the gap exists, not just restate that it exists? Are the explanations actionable? |
| **Prioritization quality** | 50 | Is the severity ranking reasonable? Are quick wins correctly identified? Does the closure plan reflect a practical verification strategy that a team could follow? |

**Deductions:**

- Gaps with vague or tautological root causes (e.g., "not tested") receive zero credit for that gap.
- Prioritization that ranks all gaps as "critical" or all as "low" receives zero prioritization points.
- Missing `closure_plan.md` results in zero prioritization points.

### Scoring Summary

| Component | Weight | Max Points |
|-----------|--------|------------|
| Automated: Gap identification | 30% | 60 |
| Judge: Completeness | -- | 100 |
| Judge: Root cause accuracy | -- | 50 |
| Judge: Prioritization quality | -- | 50 |
| **Total** | **100%** | **200** |

---

*Agentic AI Design Verification Challenge 2026 -- ISQED 2026*
