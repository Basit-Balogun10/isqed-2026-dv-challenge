# Task 3.3: The Regression Medic

## Agentic AI Design Verification Challenge 2026 -- Phase 3: Debug & Root-Cause Analysis

| Property | Value |
|----------|-------|
| **Task ID** | 3.3 |
| **Phase** | 3 -- Debug & Root-Cause Analysis |
| **Maximum Points** | 300 |
| **Per-DUT Scoring** | No (single submission) |
| **Difficulty** | 5 |
| **Estimated Effort** | 12--24 hours |
| **Evaluation Split** | Automated 65% / Judge 35% |

---

## Overview

A regression suite of 200 tests has been running nightly. Last night, 35 tests failed. Your team lead walks over and says: "Figure out what is going on. How many bugs are we looking at? Which ones matter most? And here are 5 patches from the design team -- tell me which ones actually fix something and whether any of them break something else."

This is **regression triage at scale** -- the kind of work that consumes days of a verification team's time after a bad nightly run. It requires clustering failures by root cause, prioritizing bugs, and validating proposed fixes. It is inherently agentic: no single analysis step gives you the answer. You must orchestrate multiple rounds of test execution, log analysis, failure comparison, and fix validation.

---

## Inputs Provided

| Material | Format | Description |
|----------|--------|-------------|
| Test suite | Python (cocotb) | 200 regression tests, each in its own file |
| Failure logs | `.log` files | Simulation logs for all 35 failing tests |
| Pass logs | `.log` files | Simulation logs for a representative sample of 20 passing tests (for comparison) |
| RTL source | SystemVerilog | The current (buggy) RTL that produces the 35 failures |
| 5 proposed patches | `.patch` files | Diff patches against the buggy RTL, each claiming to fix one bug |
| Test metadata | YAML | Per-test metadata including test name, target feature, expected runtime |
| Specification | Markdown | DUT specifications for context |

### Key Facts

- The 200 tests were all passing on a previous RTL version. The 35 failures are regressions caused by recent RTL changes.
- The 35 failures are caused by **approximately 5 unique bugs**. Multiple tests can fail from the same underlying bug.
- The 5 proposed patches each attempt to fix one of the 5 bugs. However:
  - Not all patches may be correct
  - A patch that fixes one bug may introduce a regression (break a previously passing test)
  - The mapping of which patch fixes which bug is not provided -- you must determine it

---

## What You Must Produce

### 1. Failure Bucketing (`bucketing.yaml`)

Group the 35 failing tests into clusters, where each cluster corresponds to one root cause (bug). You should identify approximately 5 clusters.

```yaml
clusters:
  - cluster_id: "BUG-A"
    bug_summary: "SPI clock polarity inversion in mode 3"
    failing_tests:
      - "test_spi_mode3_basic"
      - "test_spi_mode3_multiframe"
      - "test_spi_cpol1_cpha1_loopback"
      - "test_spi_all_modes_sweep"      # fails only in mode 3 iterations
    count: 4
    common_symptoms:
      - "MISO data mismatch on mode 3 transfers"
      - "SCK idle state incorrect (expected high, observed low)"
    distinguishing_signal: "SCK polarity at idle"

  - cluster_id: "BUG-B"
    bug_summary: "UART RX FIFO underflow on back-to-back reads"
    failing_tests:
      - "test_uart_rx_burst"
      - "test_uart_rx_fifo_drain"
      - "test_uart_back_to_back_rx"
      # ... more tests
    count: 8
    common_symptoms:
      - "Read data returns 0x00 instead of expected value"
      - "FIFO empty flag not set when FIFO is empty"
    distinguishing_signal: "RX FIFO read pointer vs write pointer"

  # ... more clusters
```

### 2. Root Cause Descriptions (`root_causes.md`)

For each of the ~5 bugs, provide a detailed root cause description:

- **What is broken**: The specific RTL behavior that is incorrect
- **Where it is broken**: Module name, approximate line range, signal names
- **Why it is broken**: The mechanism of the failure (e.g., missing edge detection, incorrect state transition, wrong reset value)
- **Impact scope**: Which features and test categories are affected
- **Severity assessment**: How critical is this bug (blocks functionality, causes data corruption, cosmetic, etc.)

### 3. Priority Ranking (`priority.yaml`)

Rank the ~5 bugs from highest to lowest priority, with justification:

```yaml
priority:
  - rank: 1
    cluster_id: "BUG-B"
    severity: "critical"
    rationale: >
      Data corruption on RX path affects all UART receive operations.
      8 of 35 failures trace to this bug. The FIFO underflow can cause
      silent data loss in any receive-heavy test scenario. This bug
      would be a blocking issue in silicon.

  - rank: 2
    cluster_id: "BUG-A"
    severity: "high"
    rationale: >
      SPI mode 3 is non-functional. While only 4 tests fail, SPI mode 3
      is a commonly used configuration. However, modes 0, 1, and 2 are
      unaffected, so this is a partial loss of functionality.

  # ... remaining bugs
```

### 4. Patch Validation (`patch_validation.yaml`)

For each of the 5 proposed patches, determine:

- **Which bug does it fix?** Map each patch to a cluster ID.
- **Does it actually fix the bug?** Run the failing tests from that cluster with the patch applied. Report pass/fail.
- **Does it introduce regressions?** Run the full 200-test suite with the patch applied. Report any previously-passing tests that now fail.

```yaml
patches:
  - patch_file: "patch_01.patch"
    targets_cluster: "BUG-A"
    fixes_bug: true
    tests_fixed: 4                  # of 4 in BUG-A cluster
    tests_still_failing: 0
    regressions_introduced: 0
    regression_details: []
    assessment: "Clean fix. All BUG-A failures resolved, no regressions."

  - patch_file: "patch_03.patch"
    targets_cluster: "BUG-C"
    fixes_bug: false                # Patch attempts to fix BUG-C but fails
    tests_fixed: 2                  # of 7 in BUG-C cluster
    tests_still_failing: 5
    regressions_introduced: 1
    regression_details:
      - test: "test_timer_basic_countdown"
        was: "PASS"
        now: "FAIL"
        reason: "Patch modifies timer reload logic, breaks basic countdown"
    assessment: >
      Partial fix only. Addresses one symptom of BUG-C but not the root
      cause. Additionally introduces a regression in timer countdown logic.
      Recommend rejecting this patch.

  # ... remaining patches
```

---

## Why This Task Is Agentic

This task cannot be solved with a single analysis step. It requires **orchestrating multiple activities** in sequence:

1. **Run tests** -- Execute the 200-test regression suite to reproduce the 35 failures (and confirm the 165 passes).
2. **Collect and compare failure logs** -- Gather logs from all 35 failures and identify common patterns.
3. **Cluster failures** -- Group tests by shared symptoms, error messages, failing modules, and failure mechanisms.
4. **Analyze root causes** -- For each cluster, drill into the RTL to determine the underlying bug.
5. **Apply patches** -- Apply each of the 5 patches to the RTL (one at a time).
6. **Re-run tests with patches** -- For each patch, run the relevant failure cluster to see if the bug is fixed.
7. **Check for regressions** -- For each patch, run the full suite to detect new failures.
8. **Synthesize results** -- Combine all findings into the bucketing, root cause, priority, and validation reports.

A team that manually performs each step will spend hours. A team that builds an automated pipeline -- or directs an AI agent to orchestrate these steps -- can iterate much faster and produce more thorough results.

### Workflow Diagram

```
    [Run full suite on buggy RTL]
              |
              v
    [Collect 35 failure logs + 165 pass logs]
              |
              v
    [Parse logs -> extract error signatures]
              |
              v
    [Cluster 35 failures into ~5 groups by signature similarity]
              |
              v
    [For each cluster: analyze RTL to find root cause]
              |
              v
    [Rank bugs by severity and impact]
              |
              v
    [For each patch:]
      |-> [Apply patch to RTL]
      |-> [Run cluster tests -> does patch fix the bug?]
      |-> [Run full suite -> any regressions?]
      |-> [Record results]
              |
              v
    [Compile final reports]
```

---

## Submission Format

```
submission-3.3/
├── bucketing.yaml             -- Failure clustering (required)
├── root_causes.md             -- Detailed root cause descriptions (required)
├── priority.yaml              -- Bug priority ranking with rationale (required)
├── patch_validation.yaml      -- Patch assessment results (required)
├── scripts/                   -- Optional: automation scripts
│   ├── run_regression.py
│   ├── cluster_failures.py
│   ├── apply_and_test.py
│   └── ...
├── logs/                      -- Optional: collected/processed logs
├── methodology.md             -- AI tools, orchestration approach, pipeline design
└── metadata.yaml              -- Team info, task ID
```

---

## Evaluation Rubric

### Automated Evaluation (65% -- 195 pts)

The automated evaluator checks your bucketing, fix-to-bug mapping, and regression detection against ground truth.

| Criterion | Points | Method |
|-----------|--------|--------|
| **Bucketing accuracy** | 100 | Each of the 35 failing tests has a ground-truth cluster assignment. Your clustering is compared using adjusted Rand index (ARI). ARI = 1.0 (perfect match) earns 100 pts. ARI = 0.5 earns 50 pts. ARI < 0.1 earns 0 pts. Linear interpolation between thresholds. |
| **Fix-to-bug mapping** | 50 | For each of the 5 patches, the evaluator checks whether your `targets_cluster` field correctly maps the patch to the right bug cluster. 10 pts per correct mapping. |
| **Regression detection** | 50 | For each of the 5 patches, the evaluator checks whether you correctly identified all regressions introduced by that patch. Scoring: 10 pts per patch with fully correct regression assessment (correct count and correct test names). Partial credit: 5 pts if the regression count is correct but test names are incomplete. |

**Deductions:**

- YAML files that do not parse: 0 pts for that section
- Missing required files: 0 pts for the corresponding criterion
- Clusters that contain tests from different ground-truth bugs: reduces ARI score

### Judge Evaluation (35% -- 105 pts)

| Criterion | Points | What Judges Look For |
|-----------|--------|----------------------|
| **Root cause descriptions** | 50 | Are the ~5 root cause descriptions correct, specific, and actionable? Does each description identify the exact RTL mechanism, not just the symptom? Do the descriptions distinguish root causes from one another clearly? |
| **Priority ranking rationale** | 50 | Is the severity ranking reasonable and well-justified? Does the rationale consider impact scope (how many tests affected), failure mode (data corruption vs. cosmetic), and functional importance? Would a verification lead agree with this prioritization? |
| **Triage methodology** | 5 | Is the overall triage process well-organized? Does the submission demonstrate a systematic approach to failure analysis? |

**Judge scoring for root causes:**

| Score (per bug) | Criteria |
|-----------------|----------|
| 10 pts | Correct, specific root cause with accurate module/signal identification |
| 7 pts | Correct root cause but missing precision on exact mechanism |
| 3 pts | Partially correct -- right area of the design but wrong mechanism |
| 0 pts | Incorrect or missing |

**Judge scoring for priority ranking:**

| Score | Criteria |
|-------|----------|
| 50 pts | Ranking matches expert assessment; rationale is thorough and considers multiple severity dimensions |
| 35 pts | Ranking is mostly correct (1-2 bugs swapped); rationale is reasonable |
| 20 pts | Ranking has significant disagreements with expert assessment but rationale shows understanding |
| 0 pts | Ranking is arbitrary or rationale is absent |

### Scoring Summary

| Component | Weight | Max Points |
|-----------|--------|------------|
| Automated: Bucketing accuracy | -- | 100 |
| Automated: Fix-to-bug mapping | -- | 50 |
| Automated: Regression detection | -- | 50 |
| Judge: Root cause descriptions | -- | 50 |
| Judge: Priority ranking rationale | -- | 50 |
| Judge: Triage methodology | -- | 5 |
| **Total** | **100%** | **300** |

**Note:** The judge component sums to 105 raw points, which equals the 35% allocation (105 / 300 = 35%).

---

*Agentic AI Design Verification Challenge 2026 -- ISQED 2026*
