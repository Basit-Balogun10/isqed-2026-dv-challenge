# Task 3.2: The Trace Detective

## Agentic AI Design Verification Challenge 2026 -- Phase 3: Debug & Root-Cause Analysis

| Property | Value |
|----------|-------|
| **Task ID** | 3.2 |
| **Phase** | 3 -- Debug & Root-Cause Analysis |
| **Maximum Points** | 400 |
| **Per-DUT Scoring** | No (single submission covering all 5 failures) |
| **Difficulty** | 4 |
| **Estimated Effort** | 12--20 hours |
| **Evaluation Split** | Automated 45% / Judge 55% |

---

## Overview

Task 3.1 gave you logs. This task gives you **waveforms**.

You will receive 5 complex simulation failures, each accompanied by a full VCD waveform file spanning 1,000+ clock cycles, the failing assertion or check, the relevant specification requirement, and the DUT's RTL source. Your job is to work backward from the failure symptom to the root cause -- tracing signal dependencies through the design hierarchy, across clock cycles, to the exact point where correct behavior diverged from actual behavior.

This is the most demanding debug task in the competition. It requires **temporal causality reasoning**: understanding not just which signals are wrong, but *when* they went wrong, *why* they went wrong, and *which upstream signal change* caused the downstream failure. This is a skill that separates senior verification engineers from junior ones -- and it is a skill where AI assistance is still nascent.

---

## Inputs Provided

For each of the 5 failures, you receive:

| Material | Format | Description |
|----------|--------|-------------|
| VCD waveform | `.vcd` file | Full signal dump, 1,000+ cycles, all signals in design hierarchy |
| Failing assertion | Text | The SVA property or cocotb check that failed, with the manifestation cycle |
| Specification requirement | Markdown excerpt | The spec clause that the assertion is checking |
| RTL source | SystemVerilog | Full DUT source with hierarchy information |
| Testbench source | Python (cocotb) | The test that produced the failure |
| Signal map | YAML | Mapping of key signal names to their hierarchical paths |

### VCD File Characteristics

- **Size**: 5--50 MB per failure (compressed). These are not trivial waveforms.
- **Duration**: 1,000 to 10,000 clock cycles per failure.
- **Signal count**: 200--2,000 signals per DUT, including internal hierarchy.
- **Format**: Standard IEEE VCD, compatible with GTKWave and Surfer.

The VCD files contain the full signal history for every register, wire, and port in the design. The challenge is not accessing the data -- it is knowing which signals to examine and at which cycles.

---

## What You Must Produce

### Per-Failure Analysis (`analysis/failure_XX.yaml`)

For each of the 5 failures:

```yaml
failure_id: "failure_01"
dut: "citadel_spi"

manifestation:
  cycle: 4827                     # Exact cycle where the assertion fails
  assertion: "spi_mosi_data_check"
  observed_value: "0x3C"
  expected_value: "0x5A"
  signal: "dut.u_spi_core.mosi_o"

root_cause:
  cycle: 4791                     # Cycle where the root cause occurs
  module: "citadel_spi_txfifo"
  signal: "dut.u_spi_core.u_txfifo.rptr"
  description: >
    The TX FIFO read pointer increments twice on a single pop operation
    when the FIFO transitions from full to not-full state. This occurs
    because the pop_valid signal is held high for two cycles instead of
    one when the full flag de-asserts, due to a missing edge-detection
    on the full-to-not-full transition in the FIFO control logic.

debug_trace:
  - cycle: 4791
    signal: "dut.u_spi_core.u_txfifo.full"
    value: "1 -> 0"
    note: "FIFO transitions from full to not-full as SPI shift register consumes a byte"

  - cycle: 4791
    signal: "dut.u_spi_core.u_txfifo.pop_valid"
    value: "1"
    note: "Pop valid asserted (correct -- data being consumed)"

  - cycle: 4792
    signal: "dut.u_spi_core.u_txfifo.pop_valid"
    value: "1"
    note: "Pop valid still asserted (BUG -- should have de-asserted)"

  - cycle: 4792
    signal: "dut.u_spi_core.u_txfifo.rptr"
    value: "3 -> 5"
    note: "Read pointer increments by 2 instead of 1 (double pop)"

  - cycle: 4793
    signal: "dut.u_spi_core.tx_data"
    value: "0x3C"
    note: "Wrong byte loaded into shift register (skipped 0x5A at index 4)"

  - cycle: 4827
    signal: "dut.u_spi_core.mosi_o"
    value: "0x3C"
    note: "Wrong data appears on MOSI -- assertion fires"

  reasoning: >
    The failure manifests 36 cycles after the root cause because the SPI
    shift register must clock out the current byte (8 bits x 4 SPI clocks
    per bit = 32 SPI cycles, plus 4 cycles of inter-byte gap) before the
    corrupted data appears on MOSI.

reproduction_test:
  description: >
    Fill the TX FIFO to capacity, then initiate a multi-byte SPI transfer.
    Verify that the byte sequence on MOSI exactly matches the FIFO write
    order, specifically checking the byte immediately after the FIFO
    transitions from full to not-full.
  test_code: |
    @cocotb.test()
    async def test_txfifo_full_to_notfull_pop(dut):
        """Reproduce double-pop bug at FIFO full-to-not-full transition."""
        tb = SpiTestbench(dut)
        await tb.reset()
        await tb.configure(cpol=0, cpha=0, clk_div=4)

        # Fill FIFO to capacity
        test_data = [0x10 + i for i in range(FIFO_DEPTH)]
        for byte in test_data:
            await tb.write_tx_fifo(byte)

        # Verify FIFO is full
        status = await tb.read_status()
        assert status & TX_FULL_BIT

        # Start SPI transfer -- FIFO will drain
        await tb.start_transfer(length=FIFO_DEPTH)

        # Collect bytes from MOSI
        received = await tb.capture_mosi_bytes(count=FIFO_DEPTH)

        # Verify exact byte ordering
        for i, (exp, act) in enumerate(zip(test_data, received)):
            assert exp == act, (
                f"Byte {i}: expected 0x{exp:02X}, got 0x{act:02X} "
                f"(FIFO full->not-full transition bug)"
            )
```

### Summary Report (`summary.md`)

A markdown document providing:

- **Failure overview table**: All 5 failures with manifestation cycle, root cause cycle, latency (cycles between cause and symptom), and one-line description
- **Debug methodology**: How you approached each failure -- which signals you examined first, how you narrowed down the root cause cycle, and what tools or techniques you used
- **Difficulty assessment**: Which failures were hardest and why

---

## Why This Task Is Hard for AI

Trace debugging requires a form of reasoning that current AI systems find challenging: **temporal causality across clock cycles**.

Consider the difficulty: a signal is wrong at cycle 4827. The root cause occurred at cycle 4791 -- 36 cycles earlier, in a different module, on a different signal. Between cause and effect, the corruption propagated through a FIFO, a multiplexer, a shift register, and an output buffer. To trace this path, you need to:

1. **Identify which signal is directly wrong** at the manifestation cycle
2. **Ask: what drives this signal?** and look at the driver's inputs one cycle earlier
3. **Repeat step 2** backward through the hierarchy, following data dependencies and control dependencies, potentially jumping across module boundaries
4. **Track temporal offsets** -- a FIFO introduces latency, a shift register introduces bit-serial delay, a pipeline introduces stage-by-stage delay
5. **Distinguish symptoms from causes** -- many signals will be wrong after the root cause, but only one is the originating fault

This backward-chaining, temporally-aware reasoning is the core challenge. The teams that solve it will demonstrate a genuinely valuable AI capability.

### Practical Tips

- **Start from the assertion.** Read the assertion or check to understand what property was violated and at which cycle.
- **Use the VCD strategically.** Do not dump the entire VCD into an LLM. Instead, extract signal values at specific cycles for the signals you are investigating.
- **Follow the data path.** If the wrong data appeared at an output, trace it backward: output register <- mux select <- FIFO read <- FIFO write <- input register.
- **Look for the divergence point.** Find the earliest cycle where actual behavior differs from expected behavior. That is your root cause candidate.
- **Write the reproduction test early.** A minimal test that triggers the same failure is strong evidence that you found the right root cause.

---

## Submission Format

```
submission-3.2/
├── analysis/
│   ├── failure_01.yaml        -- Per-failure analysis (required, one per failure)
│   ├── failure_02.yaml
│   ├── failure_03.yaml
│   ├── failure_04.yaml
│   └── failure_05.yaml
├── reproduction_tests/
│   ├── test_repro_01.py       -- Minimal reproduction test per failure
│   ├── test_repro_02.py
│   ├── test_repro_03.py
│   ├── test_repro_04.py
│   └── test_repro_05.py
├── summary.md                 -- Debug methodology and observations
├── methodology.md             -- AI tools, VCD analysis approach, prompt strategies
├── Makefile                   -- Build and run reproduction tests
└── metadata.yaml              -- Team info, task ID
```

---

## Evaluation Rubric

### Automated Evaluation (45% -- 180 pts)

The automated evaluator checks two things: whether you identified the correct manifestation cycle and whether your reproduction test actually triggers the bug.

| Criterion | Per Failure | Total (5 failures) | Method |
|-----------|-------------|---------------------|--------|
| **Correct manifestation cycle** | 15 pts | 75 pts | The `manifestation.cycle` field must match the ground-truth cycle within a tolerance of +/- 2 cycles. Exact match: 15 pts. Within tolerance: 10 pts. |
| **Reproduction test triggers bug** | 30 pts | 150 pts | The reproduction test is compiled and run against the buggy RTL. If it fails (detecting the bug), full points. If it passes (missing the bug), 0 pts. Partial credit: 15 pts if the test exercises the correct module but does not trigger the exact failure. |

**Penalties:**

- Reproduction test that does not compile: 0 pts for that failure
- Reproduction test that fails on clean (non-buggy) RTL: 0 pts (false positive)
- Reproduction test that exceeds 60-second timeout: scored based on output up to timeout

### Judge Evaluation (55% -- 220 pts)

| Criterion | Per Failure | Total (5 failures) | What Judges Look For |
|-----------|-------------|---------------------|----------------------|
| **Signal trace quality** | 30 pts | 150 pts | Does the debug trace accurately follow the signal dependency chain from symptom to root cause? Are the cycle numbers correct? Are the signal values accurate? Does the reasoning explain the temporal relationship between cause and effect? |
| **RTL root cause location** | 25 pts | 125 pts | Is the identified root cause module and mechanism correct? Is the description specific enough to guide a fix? Does the analysis distinguish the root cause from downstream symptoms? |

**Judge scoring per failure for signal trace:**

| Score | Criteria |
|-------|----------|
| 30 pts | Complete, accurate trace from symptom to root cause with correct cycle numbers, signal values, and causal reasoning |
| 20 pts | Correct root cause identified with mostly accurate trace but some missing intermediate steps or minor cycle errors |
| 10 pts | Root cause area identified but trace is incomplete or contains significant inaccuracies |
| 0 pts | Incorrect root cause or no meaningful trace provided |

**Judge scoring per failure for RTL root cause:**

| Score | Criteria |
|-------|----------|
| 25 pts | Exact root cause module, signal, and mechanism identified correctly |
| 15 pts | Correct module and general mechanism but imprecise about the exact signal or condition |
| 5 pts | Correct module but wrong mechanism |
| 0 pts | Wrong module or no analysis |

**Note:** Judge points are capped at the stated maximums (150 + 125 = 275 raw), then scaled to the 220-point allocation.

### Scoring Summary

| Component | Weight | Max Points |
|-----------|--------|------------|
| Automated: Correct manifestation cycle | -- | 75 |
| Automated: Reproduction test triggers bug | -- | 150 |
| Judge: Signal trace quality | -- | ~120 (scaled from 150) |
| Judge: RTL root cause location | -- | ~100 (scaled from 125) |
| **Total** | **100%** | **400** |

---

*Agentic AI Design Verification Challenge 2026 -- ISQED 2026*
