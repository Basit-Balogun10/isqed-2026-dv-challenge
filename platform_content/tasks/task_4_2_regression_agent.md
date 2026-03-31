# Task 4.2: The Regression Agent

**Phase 4 | 500 points | Difficulty: 5/5**

---

## Overview

Build a CI/CD verification agent that operates on a **live stream of RTL commits**. For each commit in the stream, your agent must assess its impact, determine which tests are affected, run the appropriate subset, analyze results, and deliver a verdict -- all without human intervention.

This task mirrors the real-world workflow of a verification engineer monitoring a design repository. Every commit that lands on the integration branch needs a verdict: is this safe to merge? Did it introduce a bug? Did it cause a coverage regression? The difference here is that your agent must make these decisions autonomously, accurately, and fast.

---

## The Commit Stream

Your agent will receive a stream of **20 commits** replayed over a **2-hour evaluation window**. Commits arrive at irregular intervals (between 2 and 15 minutes apart), simulating realistic development activity.

The stream operates against a single DUT (one of the 7 competition DUTs, selected at evaluation time) with a provided baseline verification environment.

### Commit Categories

| Category | Count | Description |
|----------|-------|-------------|
| **Benign** | 8 | Refactors, optimizations, non-functional changes, new features that are correctly implemented. The agent should return PASS. |
| **Bug-Introducing** | 6 | Commits that introduce functional bugs (off-by-one errors, incorrect state transitions, missing edge-case handling, protocol violations). The agent should return FAIL with details. |
| **Bug-Fix** | 4 | Commits that fix previously introduced bugs. The agent should return PASS and recognize the fix. |
| **Coverage-Affecting** | 2 | Commits that restructure RTL in ways that change coverage characteristics (unreachable code removal, FSM refactoring). The agent should detect coverage changes and return COVERAGE_REGRESSION if coverage drops. |

Commits are **not** presented in a predictable order. Bug-fix commits do not necessarily follow their corresponding bug-introducing commits immediately.

---

## Agent Interface

### Input: Commit Notification

Each commit is delivered as a JSON payload to your agent's HTTP endpoint or via stdin (your choice):

```json
{
  "commit_id": "a1b2c3d4",
  "timestamp": "2026-04-06T15:23:41Z",
  "author": "dev_alice",
  "message": "Optimize TX FIFO write path for single-cycle throughput",
  "diff": "--- a/rtl/nexus_uart_tx.sv\n+++ b/rtl/nexus_uart_tx.sv\n@@ -47,8 +47,7 @@\n ...",
  "files_changed": ["rtl/nexus_uart_tx.sv"],
  "rtl_snapshot_dir": "/workspace/rtl_snapshot_a1b2c3d4/"
}
```

| Field | Description |
|-------|-------------|
| `commit_id` | Short hash identifying the commit |
| `timestamp` | When the commit was made |
| `author` | Simulated developer name |
| `message` | Commit message (may or may not be accurate -- treat with skepticism) |
| `diff` | Unified diff of all changed files |
| `files_changed` | List of modified file paths |
| `rtl_snapshot_dir` | Directory containing the full RTL after this commit is applied |

### Output: Verdict

Your agent must return a structured verdict for each commit:

```json
{
  "commit_id": "a1b2c3d4",
  "verdict": "FAIL",
  "confidence": 0.92,
  "processing_time_seconds": 127,
  "tests_run": 14,
  "tests_passed": 11,
  "tests_failed": 3,
  "details": {
    "bug_description": "TX FIFO write optimization removes the full-flag check, allowing writes to a full FIFO. Data is silently dropped when FIFO depth exceeds 16 entries.",
    "affected_module": "nexus_uart_tx",
    "affected_lines": [49, 50],
    "severity": "high",
    "failing_tests": [
      "test_tx_fifo_overflow",
      "test_tx_burst_max_depth",
      "test_tx_random_stress"
    ],
    "root_cause": "Removed condition `if (!tx_fifo_full)` on line 49, unconditionally writing to FIFO pointer.",
    "suggested_fix": "Restore the FIFO full check before incrementing the write pointer."
  },
  "coverage_delta": {
    "line_coverage_change": -0.3,
    "branch_coverage_change": -1.2,
    "functional_coverage_change": 0.0
  }
}
```

#### Verdict Values

| Verdict | When to Use |
|---------|-------------|
| `PASS` | Commit is clean. All affected tests pass. No coverage regression. |
| `FAIL` | Commit introduces a functional bug. Must include `bug_description`, `affected_module`, `severity`, and `failing_tests` in details. |
| `COVERAGE_REGRESSION` | Commit causes measurable coverage loss without introducing a functional bug. Must include `coverage_delta` showing the regression. |

---

## Entry Point

Your agent must be startable with:

```bash
python run_regression_agent.py \
  --baseline_rtl <path> \
  --baseline_env <path> \
  --listen <mode>
```

**Arguments:**

| Flag | Description |
|------|-------------|
| `--baseline_rtl` | Directory containing the baseline (pre-stream) RTL |
| `--baseline_env` | Directory containing the baseline cocotb/pyuvm verification environment and tests |
| `--listen` | Communication mode: `http` (agent runs HTTP server on port 8080) or `stdin` (reads JSON from stdin, writes to stdout) |

The agent is started once before the stream begins. It should initialize by analyzing the baseline RTL and environment, then wait for commits.

---

## What Makes This Hard

### 1. Impact Analysis

Not every commit requires running the full test suite. A change to `uart_tx.sv` should not trigger I2C tests. Your agent must perform **impact analysis** on each diff to determine:

- Which RTL modules are affected (directly changed + downstream dependents)
- Which tests exercise those modules
- Whether new tests need to be generated for new/changed functionality

### 2. Speed vs. Thoroughness

Running the full regression suite for every commit is safe but slow. Running only a handful of targeted tests is fast but risky. The optimal agent balances these concerns:

- Use the diff to assess risk level
- High-risk changes (FSM modifications, control logic) warrant broader test coverage
- Low-risk changes (comment updates, wire renaming) can be verified with a minimal smoke test
- The speed bonus rewards agents that average under 3 minutes per commit

### 3. Stateful Reasoning

Commits are not independent. A bug introduced in commit 5 may be fixed in commit 12. Your agent should maintain state across the stream:

- Track known bugs and which commits introduced them
- Recognize when a bug-fix commit resolves a previously identified issue
- Detect when a "fix" introduces a new bug while resolving the old one

### 4. Coverage Tracking

The agent must maintain a running coverage model and detect when a commit causes coverage to drop, even if all tests still pass. This requires:

- Baseline coverage measurement during initialization
- Per-commit coverage collection
- Delta analysis with meaningful thresholds (not every 0.1% fluctuation is a regression)

---

## Example Agent Workflow

```
1. INITIALIZE
   ├── Parse baseline RTL (module hierarchy, dependency graph)
   ├── Index baseline test suite (which tests target which modules)
   ├── Run baseline regression to establish coverage baseline
   └── Build dependency map: module → tests → coverage bins

2. PER COMMIT
   ├── Receive commit payload
   ├── ANALYZE DIFF
   │   ├── Parse unified diff
   │   ├── Identify changed modules
   │   ├── Classify change type (refactor, logic change, new feature, etc.)
   │   └── Assess risk level (low / medium / high / critical)
   ├── SELECT TESTS
   │   ├── Query dependency map for affected tests
   │   ├── Add broader tests if risk is high
   │   └── Optionally generate new targeted tests for new functionality
   ├── RUN TESTS
   │   ├── Apply commit to RTL snapshot
   │   ├── Compile environment + updated RTL
   │   ├── Execute selected test subset
   │   └── Collect results and coverage
   ├── ANALYZE RESULTS
   │   ├── Check for test failures → classify as bug or false positive
   │   ├── Compare coverage against baseline → detect regressions
   │   ├── Cross-reference with known bugs from previous commits
   │   └── If bug detected: identify root cause from diff + failure logs
   └── EMIT VERDICT
       └── Return structured JSON verdict
```

---

## Submission Format

```
submission/
  task_4_2/
    run_regression_agent.py     — Entry point
    requirements.txt            — Python dependencies
    agent/                      — Your agent source code
    config/                     — Configuration files
    README.md                   — Architecture overview, setup instructions
```

The platform will execute your agent in a sandboxed environment with:

- Python 3.11+
- cocotb 1.9+, pyuvm latest
- Icarus Verilog 12+ and Verilator 5.x
- Network access (for LLM API calls only)
- 16 GB RAM, 8 CPU cores
- 2-hour wall-clock limit for the full 20-commit stream

---

## Evaluation Rubric

### Automated Scoring (85% -- 425 points)

Each commit in the stream is scored independently. Points are summed across all 20 commits.

| Category | Points | Criteria |
|----------|--------|----------|
| **Correct PASS on benign commit** | 15 pts each (x8 = 120 pts max) | Agent correctly identifies a benign commit and returns PASS. No false alarm raised. |
| **Correct FAIL with bug details** | 40 pts each (x6 = 240 pts max) | Agent correctly identifies a bug-introducing commit, returns FAIL, and provides an accurate bug description with affected module and root cause. Partial credit (20 pts) for correct FAIL verdict without accurate details. |
| **Correct bug-fix recognition** | 25 pts each (x4 = 100 pts max) | Agent correctly identifies a bug-fix commit, returns PASS, and notes the fix in the details. Partial credit (15 pts) for correct PASS without recognizing it as a fix. |
| **Correct coverage regression** | 25 pts each (x2 = 50 pts max) | Agent correctly identifies a coverage-affecting commit and returns COVERAGE_REGRESSION with accurate delta metrics. Partial credit (15 pts) for detecting the coverage change without accurate quantification. |
| **False positive penalty** | -20 pts each | Agent returns FAIL or COVERAGE_REGRESSION for a benign commit. Strongly penalized to discourage conservative "flag everything" strategies. |
| **False negative penalty** | -40 pts each | Agent returns PASS for a bug-introducing commit. The most severe penalty -- missing bugs is the worst outcome in verification. |
| **Speed bonus** | 50 pts | Awarded if the agent's average per-commit processing time (from receiving the commit to emitting the verdict) is under 3 minutes across all 20 commits. |

**Maximum possible automated score:** 120 + 240 + 100 + 50 + 50 = 560 pts (before penalties). Capped at 425 pts (85% of 500).

### Judge Scoring (15% -- 75 points)

| Category | Points | Criteria |
|----------|--------|----------|
| **Architecture Sophistication** | 0--25 pts | Quality of the impact analysis engine. Dependency graph construction. Test selection strategy. |
| **Stateful Reasoning** | 0--25 pts | Ability to track bugs across the commit stream. Recognition of fix-introduces-new-bug patterns. Context accumulation over time. |
| **Efficiency** | 0--25 pts | Test selection precision (ratio of useful tests run to total tests available). LLM usage efficiency. Resource management. |

---

## Tips for Success

1. **Invest in initialization.** The minutes you spend during startup building a module dependency graph and indexing the test suite pay dividends on every subsequent commit. A well-indexed baseline turns impact analysis from an LLM-intensive task into a graph traversal.

2. **Do not run all tests for every commit.** The speed bonus is worth 50 points, and the penalty structure rewards precision. An agent that runs 5 well-chosen tests in 90 seconds outperforms one that runs 50 tests in 10 minutes -- if the 5 tests are the right ones.

3. **Parse the diff carefully.** The unified diff is your primary signal. Look for changes to `always` blocks, state machine transitions, conditional logic, and signal assignments. A comment-only change should take seconds to clear as PASS.

4. **Maintain a bug ledger.** Track every bug you identify, which commit introduced it, and which signals/modules it affects. When a later commit touches the same area and tests start passing again, you can confidently flag it as a bug-fix.

5. **Set meaningful coverage thresholds.** Not every coverage fluctuation is a regression. Normal test randomness causes small variations. Establish a baseline variance (e.g., +/- 0.5%) and only flag regressions that exceed it.

6. **Handle compilation failures gracefully.** Some commits may not compile cleanly (intentionally or due to incomplete changes). Your agent should detect this, report it as a FAIL with "compilation error" details, and move on to the next commit without crashing.
