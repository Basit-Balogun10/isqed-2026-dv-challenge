# Task 2.2: Stimulus Engineering

## Agentic AI Design Verification Challenge 2026 -- Phase 2: Coverage Closure Campaign

| Property | Value |
|----------|-------|
| **Task ID** | 2.2 |
| **Phase** | 2 -- Coverage Closure Campaign |
| **Maximum Points** | 2000 (500 per DUT, up to 4 DUTs) |
| **Per-DUT Scoring** | Yes (max 4 DUTs scored) |
| **Difficulty** | 4 |
| **Estimated Effort** | 12--24 hours |
| **Evaluation Split** | Automated 95% / Judge 5% |

---

## Overview

This is the **primary competition differentiator** -- the highest point value among all Phase 2 tasks and the task where the gap between strong and weak teams will be most visible.

Your objective: write tests and sequences that **close coverage gaps** in the reference testbench. The reference testbenches achieve roughly 40% line, 30% branch, and 20% functional coverage. Your job is to push those numbers toward the 90%/85%/85% targets defined in the competition.

Every percentage point of coverage improvement earns points. Every FSM state and transition you reach earns bonuses. Every functional coverage bin you hit compounds your score. The scoring formula is transparent and entirely metrics-driven -- there is no subjectivity in 95% of this task's evaluation.

---

## Inputs Provided

For each DUT, you receive:

| Material | Format | Description |
|----------|--------|-------------|
| Reference testbench | Python (cocotb) | Baseline testbench achieving ~40% line coverage |
| Reference coverage data | `.dat` + HTML | Coverage results from the reference testbench |
| RTL source | SystemVerilog | Full DUT source under `duts/<dut_name>/` |
| Specification | Markdown | DUT behavior specification |
| CSR map | Hjson | Register definitions, fields, access types, reset values |
| Verification plan | YAML | Feature list with coverage targets |
| Functional coverage model | Python | Baseline covergroups (may be incomplete) |

You may also use your own output from Task 2.1 (Coverage Gap Analysis) as input to guide your stimulus strategy.

---

## What You Must Produce

### 1. New Test Sequences

Write tests that exercise uncovered RTL behavior. These fall into two categories:

**Constrained-random sequences** -- Randomized stimulus with constraints tuned to reach specific coverage regions:

```python
# Example: Constrained-random sequence targeting UART parity modes
@cocotb.test()
async def test_uart_parity_modes(dut):
    """Exercise all parity configurations with randomized data patterns."""
    tb = UartTestbench(dut)
    await tb.reset()

    parity_modes = [PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE]

    for mode in parity_modes:
        await tb.configure(parity=mode, baud=115200)
        for _ in range(20):
            data = random.randint(0, 0xFF)
            await tb.transmit(data)
            received = await tb.receive()
            assert received == data, f"Mismatch in parity mode {mode}"
```

**Directed corner-case tests** -- Targeted tests that hit specific hard-to-reach states:

```python
# Example: Directed test for FIFO overflow behavior
@cocotb.test()
async def test_tx_fifo_overflow(dut):
    """Verify TX FIFO overflow handling: write beyond capacity, check status."""
    tb = UartTestbench(dut)
    await tb.reset()
    await tb.configure(baud=9600)

    # Fill FIFO to capacity
    for i in range(FIFO_DEPTH):
        await tb.write_tx_fifo(i & 0xFF)

    # Attempt one more write -- should set overflow status
    await tb.write_tx_fifo(0xAA)
    status = await tb.read_status()
    assert status & TX_OVERFLOW_BIT, "Overflow bit not set after FIFO overflow"
```

### 2. Updated Coverage Model (if applicable)

If the baseline functional coverage model is incomplete, you may extend it with additional coverpoints, bins, and crosses. New coverage definitions must be clearly separated from the baseline model.

### 3. Updated Coverage Results

Run your complete test suite (reference tests + your new tests) and include the resulting coverage data. This is what the automated evaluator scores.

---

## Scoring Formula

Coverage improvement is measured as the delta between the reference testbench baseline and your submission's results. Points are awarded per DUT according to the following formula:

### Per-DUT Scoring Breakdown (500 pts max per DUT)

| Metric | Points per Percentage Point Improvement | Notes |
|--------|----------------------------------------|-------|
| **Line coverage** | 5 pts | Measured by Verilator `--coverage-line` |
| **Branch coverage** | 7 pts | Measured by Verilator `--coverage-branch`; harder to close than line |
| **Toggle coverage** | 3 pts | Measured by Verilator `--coverage-toggle` |
| **Functional coverage** | 8 pts | Measured via cocotb-coverage covergroups |

### Bonus Points

| Achievement | Bonus |
|-------------|-------|
| **FSM state coverage reaches 100%** | +50 pts |
| **FSM transition coverage reaches 100%** | +100 pts |
| **Each new cross-coverage bin hit** | +5 pts per bin |

### Example Calculation

Starting from the reference baseline for `nexus_uart`:

| Metric | Baseline | Your Result | Delta | Points |
|--------|----------|-------------|-------|--------|
| Line | 42% | 78% | +36% | 180 |
| Branch | 31% | 69% | +38% | 266 |
| Toggle | 25% | 55% | +30% | 90 |
| Functional | 18% | 52% | +34% | 272 |
| FSM states | 60% | 100% | -- | +50 |
| FSM transitions | 40% | 85% | -- | 0 |
| Cross bins | 0 | 12 new | -- | +60 |
| **Subtotal** | | | | **918** |
| **Capped at 500** | | | | **500** |

Each DUT is scored independently and capped at 500 points. Your total Task 2.2 score is the sum across your best 4 DUTs (max 2000 pts).

### DUT Tier Weighting

DUT difficulty tier multipliers apply to the raw score before the 500-point cap:

| DUT | Tier | Multiplier |
|-----|------|------------|
| nexus_uart, bastion_gpio | 1 | 1.0x |
| warden_timer, citadel_spi | 2 | 1.5x |
| aegis_aes, sentinel_hmac | 3 | 2.0x |
| rampart_i2c | 4 | 2.5x |

This means a 10-point improvement on `rampart_i2c` is worth 25 points before capping -- higher-tier DUTs are more rewarding.

---

## The AI-Driven Coverage Closure Loop

This task is purpose-built to demonstrate a core AI verification capability: **reasoning backward from uncovered code to the stimulus needed to reach it.**

The key insight is that LLMs can read annotated RTL source -- where uncovered lines are highlighted -- and reason about what input conditions would cause execution to reach those lines. This transforms coverage closure from a manual, intuition-driven process into a systematic, AI-augmented loop.

### The Iterative Process

```
                    +------------------+
                    |  Run Simulation  |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Collect Coverage |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Identify Gaps    |
                    | (uncovered lines,|
                    |  unhit bins)     |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Feed Uncovered   |
                    | RTL + Context    |
                    | to LLM          |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | LLM Generates    |
                    | New Sequence     |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Add to Testbench |
                    | & Validate       |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Re-run Simulation|
                    +--------+---------+
                             |
                      (loop back to top)
```

### Effective Strategies

1. **Start with the coverage report, not the spec.** Feed your AI tool the annotated RTL source with coverage markers. Ask it: "What input stimulus would cause line 147 to execute?" The answer often reveals a missing configuration, transaction type, or error condition.

2. **Group related gaps.** Multiple uncovered lines in the same module often share a root cause. Closing one gap frequently closes several others. Analyze coverage at the block level before writing individual tests.

3. **Use the CSR map as a constraint guide.** Register fields define the configuration space. If a register field has 8 possible values and only 2 have been tested, constrain your randomization to favor the untested values.

4. **Target branch coverage aggressively.** Branch coverage is worth 7 pts per percentage point (the highest rate) and is typically the hardest to close. Focus AI-generated sequences on exercising both arms of every conditional.

5. **Build toward FSM bonuses.** The 100% FSM state and transition bonuses (50 and 100 pts respectively) are substantial. Map out FSM states from the RTL, identify unvisited states, and write directed sequences to reach them.

6. **Iterate rapidly.** Each loop iteration gives you concrete feedback. Coverage either went up (the sequence worked) or it did not (try a different approach). Aim for many short iterations rather than one long generation pass.

---

## Submission Format

```
submission-2.2-{dut_id}/
├── testbench/
│   ├── env.py                 -- Test environment (may extend reference)
│   ├── agents/                -- Agents (may reuse from Phase 1)
│   ├── scoreboard.py          -- Scoreboard (may reuse from Phase 1)
│   ├── coverage.py            -- Coverage model (baseline + extensions)
│   └── sequences/             -- New sequences targeting coverage gaps
│       ├── seq_parity_modes.py
│       ├── seq_fifo_corner.py
│       └── ...
├── tests/
│   ├── test_gap_closure.py    -- New tests (must follow test_* naming)
│   └── ...
├── results/
│   ├── coverage_report.html   -- Updated coverage from full suite run
│   ├── coverage_delta.yaml    -- Baseline vs. new coverage comparison
│   └── regression_log.txt     -- Full test suite output
├── methodology.md             -- AI tools and iteration process
├── Makefile                   -- Build and run (must support `make SIM=verilator`)
└── metadata.yaml              -- Team info, task/DUT ID
```

### Important Notes

- Your submission must include **both** the reference testbench tests and your new tests. Coverage is measured from the complete suite.
- All tests must **pass** on the clean (non-buggy) RTL. Tests that fail on correct RTL are excluded from coverage measurement and incur no direct penalty, but they waste your simulation budget.
- The 10-minute simulation timeout applies. Optimize test runtime -- 100 targeted tests beat 10,000 unfocused random iterations.

---

## Evaluation Rubric

### Automated Evaluation (95% -- 475 pts per DUT)

Coverage improvement is measured objectively by running your submission against the reference RTL with Verilator's coverage instrumentation enabled.

| Criterion | Points | Method |
|-----------|--------|--------|
| **Line coverage improvement** | 5 pts per percentage point gained | Delta from reference baseline to your result |
| **Branch coverage improvement** | 7 pts per percentage point gained | Delta from reference baseline to your result |
| **Toggle coverage improvement** | 3 pts per percentage point gained | Delta from reference baseline to your result |
| **Functional coverage improvement** | 8 pts per percentage point gained | Delta from reference baseline to your result; only bins defined in the baseline model count unless you extend it |
| **FSM state coverage 100%** | 50 pt bonus | All-or-nothing: every FSM state must be visited |
| **FSM transition coverage 100%** | 100 pt bonus | All-or-nothing: every FSM transition must be taken |
| **New cross-coverage bins** | 5 pts per new bin hit | Bins added beyond the baseline functional coverage model |
| **Test suite validity** | Required | All tests must compile and run within the 10-minute timeout |

**Penalties:**

- Tests that fail on clean RTL: excluded from coverage (no penalty, but no contribution)
- Submission that does not compile: 0 pts for that DUT
- Simulation timeout: coverage measured up to the timeout point only

### Judge Evaluation (5% -- 25 pts per DUT)

| Criterion | Points | What Judges Look For |
|-----------|--------|----------------------|
| **Stimulus design quality** | 25 | Are sequences well-structured and purposeful? Is there evidence of systematic coverage closure strategy vs. brute-force randomization? Is the code readable and maintainable? |

### Scoring Summary

| Component | Weight | Max Points (per DUT) |
|-----------|--------|----------------------|
| Automated: Coverage improvement + bonuses | 95% | 475 |
| Judge: Stimulus quality | 5% | 25 |
| **Per-DUT Total** | **100%** | **500** |
| **Task Total (best 4 DUTs)** | | **2000** |

---

*Agentic AI Design Verification Challenge 2026 -- ISQED 2026*
