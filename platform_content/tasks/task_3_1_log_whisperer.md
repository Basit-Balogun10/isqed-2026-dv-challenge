# Task 3.1: The Log Whisperer

## Agentic AI Design Verification Challenge 2026 -- Phase 3: Debug & Root-Cause Analysis

| Property | Value |
|----------|-------|
| **Task ID** | 3.1 |
| **Phase** | 3 -- Debug & Root-Cause Analysis |
| **Maximum Points** | 300 |
| **Per-DUT Scoring** | No (single submission covering all 10 failures) |
| **Difficulty** | 3 |
| **Estimated Effort** | 6--12 hours |
| **Evaluation Split** | Automated 60% / Judge 40% |

---

## Overview

Simulation logs are the front line of hardware debugging. When a test fails, the first thing a verification engineer sees is the log: a wall of UVM messages, scoreboard mismatches, assertion violations, and truncated signal traces -- interspersed with thousands of lines of normal operation.

Your task is to **triage 10 simulation failures** from their log output alone. For each failure, you must classify it, identify where in the design it originates, explain the root cause, and suggest a fix. This is the daily work of a verification engineer, and it is a task where AI can provide exceptional leverage -- if the noise can be filtered from the signal.

---

## Inputs Provided

You will receive **10 simulation failure logs**, each between 500 and 5,000 lines. Each log corresponds to a single test run that ended in failure on one of the competition DUTs.

| Material | Format | Description |
|----------|--------|-------------|
| Failure logs | `.log` text files | 10 simulation logs, each from a failing test |
| RTL source | SystemVerilog | Full DUT source for all DUTs (for cross-referencing) |
| Testbench source | Python (cocotb) | The testbench that produced each log |
| Specification | Markdown | DUT specifications for context |

### What the Logs Contain

Each log may contain any combination of:

- **UVM/cocotb framework messages** -- Info, warning, error, and fatal messages from the verification framework
- **Scoreboard mismatches** -- Expected vs. actual transaction comparisons
- **Assertion failures** -- SVA or cocotb assertion violations with signal values at the failure time
- **Signal trace dumps** -- Partial signal value dumps around the failure point (not full VCD -- just text-formatted snapshots)
- **Protocol checker errors** -- Bus protocol violations (e.g., TL-UL handshake violations)
- **Timeout messages** -- Tests that stalled waiting for an expected event
- **Normal operation messages** -- Thousands of routine info-level messages from successful transactions before the failure

### Log Characteristics

The logs are deliberately realistic, meaning they are **noisy**:

- Multiple warnings may appear before the actual failure, some of which are benign
- Error cascades are common (one root failure triggers many secondary errors)
- Signal values may be presented in different formats (hex, binary, decimal) across different log sections
- Some logs are truncated (simulation was killed after a timeout)
- Timestamps and cycle counts are present but may not be consistently formatted

---

## What You Must Produce

### Per-Failure Analysis (`analysis/failure_XX.yaml`)

For each of the 10 failures, produce a structured YAML analysis file:

```yaml
failure_id: "failure_01"
log_file: "logs/failure_01.log"

classification:
  type: "functional_bug"          # One of: functional_bug, testbench_bug,
                                  #   protocol_violation, timing_issue,
                                  #   configuration_error
  confidence: 0.85                # 0.0 to 1.0

location:
  root_module: "nexus_uart_rx"    # RTL module where the bug originates
  line_range: "87-95"             # Approximate RTL line range
  hierarchy: "dut.u_uart_rx"      # Instance path in the design hierarchy

root_cause:
  summary: >
    The UART RX module's baud rate counter reloads with the wrong prescaler
    value when the NCO register is updated mid-frame. The counter samples
    the NCO value asynchronously, causing a glitch in the baud clock that
    shortens one bit period by 2 cycles. This causes the RX sampler to
    read the stop bit one cycle early, interpreting it as a framing error.
  evidence:
    - "Log line 342: Scoreboard mismatch -- expected 0xA5, got 0x00"
    - "Log line 338: RX framing error flag set unexpectedly"
    - "Log line 335: NCO register write at cycle 14520 (mid-frame)"
  chain_of_events:
    - "NCO register updated at cycle 14520 while RX frame in progress"
    - "Baud counter reloads with new prescaler value mid-count"
    - "Bit period shortened, sampling point shifts"
    - "Stop bit sampled at wrong time, framing error asserted"
    - "Received byte corrupted, scoreboard mismatch"

suggested_fix:
  description: >
    Gate the NCO update so the baud counter only loads new prescaler values
    at frame boundaries (when rx_idle is asserted). Alternatively, double-
    buffer the NCO value and swap at the start of each frame.
  rtl_change:
    file: "nexus_uart_rx.sv"
    approximate_location: "line 90"
    change_type: "add synchronization logic"
```

### Summary Report (`summary.md`)

A markdown document providing:

- **Failure triage table**: All 10 failures with classification, root module, and one-line summary
- **Bug clustering**: Group failures that stem from the same underlying bug (if any)
- **Cross-cutting observations**: Patterns across failures (e.g., "3 of 10 failures relate to register access timing")
- **Confidence assessment**: Which analyses you are most/least confident about and why

---

## Failure Classification Types

Your classification must use exactly one of these five types:

| Type | Description | Example |
|------|-------------|---------|
| `functional_bug` | A bug in the RTL design logic | Incorrect state machine transition, wrong data path mux select |
| `testbench_bug` | A bug in the testbench, not the DUT | Scoreboard reference model is wrong, driver sends illegal stimulus |
| `protocol_violation` | A bus or interface protocol rule is violated | TL-UL handshake timing violation, SPI clock polarity mismatch |
| `timing_issue` | A timing-related failure (race condition, setup/hold, clock domain) | Metastability on async input, clock-domain crossing glitch |
| `configuration_error` | Incorrect or missing register configuration before test stimulus | Baud rate not set before UART TX, SPI mode mismatch between host and device |

---

## Why This Task Tests AI Capabilities

Log analysis is a natural strength for language models:

- **Pattern matching**: LLMs can identify error patterns across thousands of lines of log text, picking out the critical failure signature from the noise.
- **Cross-referencing**: Given the log and RTL source, LLMs can correlate error messages with specific RTL locations.
- **Reasoning about causality**: When multiple errors appear in cascade, LLMs can often identify which error was the root cause and which were symptoms.

However, logs are adversarial inputs for naive LLM processing:

- **Volume**: A 5,000-line log contains mostly irrelevant information. A naive approach of feeding the entire log to an LLM may exceed context limits or dilute the model's attention.
- **Format inconsistency**: Different components log in different formats. The LLM must handle hex, binary, decimal, timestamps, cycle counts, and hierarchical paths.
- **Red herrings**: Benign warnings that appear before the real failure can mislead the analysis.

The most effective approach involves a **preprocessing pipeline**: parse the log to extract error and warning lines, group them by time/cycle, identify the first failure, and then feed the relevant context (not the full log) to the LLM for analysis.

---

## Submission Format

```
submission-3.1/
├── analysis/
│   ├── failure_01.yaml        -- Per-failure analysis (required, one per failure)
│   ├── failure_02.yaml
│   ├── ...
│   └── failure_10.yaml
├── summary.md                 -- Triage summary and cross-cutting observations
├── preprocessing/             -- Optional: log preprocessing scripts
│   ├── log_parser.py
│   └── error_extractor.py
├── methodology.md             -- AI tools, preprocessing pipeline, prompt strategies
└── metadata.yaml              -- Team info, task ID
```

---

## Evaluation Rubric

### Automated Evaluation (60% -- 180 pts)

The automated evaluator checks your classifications and root module identifications against ground truth for each of the 10 failures.

| Criterion | Per Failure | Total (10 failures) | Method |
|-----------|-------------|----------------------|--------|
| **Correct failure classification** | 10 pts | 100 pts | Exact match against ground-truth classification type. Partial credit: 5 pts if the classification is adjacent (e.g., `timing_issue` when the answer is `functional_bug` but the bug involves timing). |
| **Correct root module identification** | 10 pts | 100 pts | The `root_module` field must name the correct RTL module. Partial credit: 5 pts for naming a module within one level of hierarchy of the correct module. |

**Deductions:**

- Analysis files that do not parse as valid YAML: 0 pts for that failure
- Missing analysis files: 0 pts for that failure
- Extra fields beyond the schema: no penalty (ignored)

**Note:** The automated evaluator does not assess root cause descriptions or fix suggestions -- those are evaluated by judges.

### Judge Evaluation (40% -- 120 pts)

| Criterion | Per Failure | Total (10 failures) | What Judges Look For |
|-----------|-------------|----------------------|----------------------|
| **Root cause description** | 15 pts | 150 pts | Is the root cause correct? Is it specific (identifies the actual mechanism of failure) rather than generic? Does the chain of events accurately describe the failure progression? |
| **Fix suggestion** | 5 pts | 50 pts | Is the suggested fix actionable and likely to resolve the issue without introducing new bugs? Does it address the root cause rather than masking the symptom? |

**Judge scoring per failure:**

| Root Cause Score | Criteria |
|------------------|----------|
| 15 pts | Correct, specific, well-evidenced root cause with accurate chain of events |
| 10 pts | Correct root cause but missing details or incomplete chain of events |
| 5 pts | Partially correct -- identifies the right area but wrong mechanism |
| 0 pts | Incorrect or missing root cause |

| Fix Score | Criteria |
|-----------|----------|
| 5 pts | Actionable fix that addresses the root cause correctly |
| 3 pts | Reasonable fix direction but incomplete or imprecise |
| 0 pts | Incorrect, missing, or symptom-masking fix |

**Note:** Judge points are capped at the stated maximums (150 + 50 = 200 raw), then scaled to the 120-point allocation.

### Scoring Summary

| Component | Weight | Max Points |
|-----------|--------|------------|
| Automated: Classification accuracy | -- | 100 |
| Automated: Root module identification | -- | 100 |
| Judge: Root cause descriptions | -- | ~90 (scaled from 150) |
| Judge: Fix suggestions | -- | ~30 (scaled from 50) |
| **Total** | **100%** | **300** |

---

*Agentic AI Design Verification Challenge 2026 -- ISQED 2026*
