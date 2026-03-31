# Task 4.3: The Spec Interpreter

**Phase 4 | 400 points | Difficulty: 5/5**

---

## Overview

Build an agent that takes **only a natural-language specification** -- no RTL, no register map, no existing testbench -- and produces the verification artifacts that a DV engineer would create *before the design is implemented*:

1. A structured verification plan
2. Cocotb test stubs
3. A functional coverage model
4. Behavioral assertions

This task captures a critical and often underappreciated stage of the verification lifecycle. Before a single line of RTL exists, a verification engineer reads the specification and translates it into a plan: what must be tested, how coverage will be measured, and what properties any correct implementation must satisfy. Can an AI agent perform this translation?

The evaluation is heavily judge-weighted (80%) because correctness here is measured against a human expert's verification plan -- there is no single right answer, but there are clear standards of completeness, accuracy, and quality.

---

## What Your Agent Must Produce

### 1. Verification Plan (YAML)

A structured verification plan that enumerates every testable feature in the specification, organized hierarchically with coverage goals and test strategies.

```yaml
verification_plan:
  dut_name: "nexus_uart"
  spec_version: "1.0"
  author: "agent"
  date: "2026-04-06"

  features:
    - id: "F001"
      name: "Basic TX Operation"
      description: >
        The UART transmitter shall serialize data from the TX FIFO onto
        the serial output line according to the configured baud rate,
        data bits, parity, and stop bit settings.
      priority: high
      risk: medium
      coverage_goals:
        - "All supported data widths (5, 6, 7, 8 bits)"
        - "All parity modes (none, even, odd)"
        - "1 and 2 stop bits"
        - "Baud rates: 9600, 19200, 38400, 57600, 115200"
      test_strategy: >
        Directed tests for each configuration combination.
        Constrained-random for cross-product coverage.
      tests:
        - "test_tx_basic_8n1"
        - "test_tx_all_data_widths"
        - "test_tx_parity_modes"
        - "test_tx_baud_rates"
      assertions:
        - "A001: TX line idles high between frames"
        - "A002: Start bit is exactly one bit period low"
        - "A003: Data bits match FIFO content in LSB-first order"

    - id: "F002"
      name: "TX FIFO Management"
      description: >
        The TX FIFO shall accept writes via the WDATA CSR, track fill
        level, assert the tx_full interrupt when capacity is reached,
        and prevent data corruption on overflow.
      priority: high
      risk: high
      coverage_goals:
        - "FIFO empty, partially filled, full states"
        - "Write to full FIFO (overflow handling)"
        - "Back-to-back writes at maximum rate"
        - "FIFO depth boundary (15/16, 16/16)"
      test_strategy: >
        Directed tests for boundary conditions.
        Stress test with continuous writes exceeding FIFO depth.
      tests:
        - "test_tx_fifo_fill_drain"
        - "test_tx_fifo_overflow"
        - "test_tx_fifo_stress"
      assertions:
        - "A004: FIFO full flag asserts when depth reaches capacity"
        - "A005: No data loss when FIFO is not full"

    # ... additional features ...

  cross_feature_tests:
    - id: "X001"
      name: "Simultaneous TX and RX"
      features: ["F001", "F010"]
      description: "Full-duplex operation under load"
    # ...

  coverage_summary:
    total_features: 18
    total_tests: 42
    total_assertions: 31
    priority_distribution:
      high: 7
      medium: 8
      low: 3
```

### 2. Cocotb Test Stubs

Test files that express **verification intent** without referencing RTL-specific signal names. Each test stub must include:

- A clear docstring describing what is being tested and why
- Setup / precondition logic
- Stimulus description (what inputs to drive)
- Expected behavior / check logic (what to verify)
- Placeholder signal references marked for implementation-time binding

```python
"""
Test Suite: TX FIFO Management
Verification Plan Features: F002
"""

import cocotb
from cocotb.triggers import Timer, RisingEdge


# Signal bindings — to be resolved against actual RTL port names
# These are placeholders expressing the INTENT of each signal reference.
SIGNALS = {
    "clock":       "clk_i",          # Primary clock
    "reset":       "rst_ni",         # Active-low reset
    "tx_data_reg": "TBD_WDATA",      # CSR address for TX write data
    "tx_fifo_lvl": "TBD_FIFO_LVL",   # FIFO level status register
    "tx_full_irq": "TBD_TX_FULL",    # TX FIFO full interrupt
}


@cocotb.test()
async def test_tx_fifo_fill_drain(dut):
    """
    Feature: F002 — TX FIFO Management
    Goal: Verify that the TX FIFO correctly tracks fill level as data
          is written (via CSR) and drained (via serial transmission).

    Procedure:
      1. Reset the DUT and configure TX for 8N1 at 115200 baud.
      2. Write N bytes (where N = FIFO depth) to the TX data register.
      3. After each write, read the FIFO level register and verify it
         increments by 1.
      4. Wait for TX to drain each byte over the serial line.
      5. Verify FIFO level decrements as bytes are transmitted.
      6. Verify FIFO returns to empty state after all bytes are sent.

    Expected:
      - FIFO level accurately tracks occupancy at all times.
      - No data corruption in transmitted bytes.
      - FIFO empty status asserts when last byte is transmitted.
    """
    # SETUP: Initialize DUT
    await reset_dut(dut)
    await configure_uart(dut, baud=115200, data_bits=8, parity="none", stop_bits=1)

    fifo_depth = 16  # From specification

    # STIMULUS: Fill the FIFO
    test_data = [i & 0xFF for i in range(fifo_depth)]
    for i, byte in enumerate(test_data):
        await write_csr(dut, SIGNALS["tx_data_reg"], byte)
        level = await read_csr(dut, SIGNALS["tx_fifo_lvl"])
        assert level == i + 1, f"FIFO level mismatch: expected {i+1}, got {level}"

    # CHECK: Wait for drain and verify
    for i in range(fifo_depth):
        await wait_for_tx_complete(dut)
        level = await read_csr(dut, SIGNALS["tx_fifo_lvl"])
        expected_level = fifo_depth - (i + 1)
        assert level == expected_level, \
            f"Drain level mismatch: expected {expected_level}, got {level}"


@cocotb.test()
async def test_tx_fifo_overflow(dut):
    """
    Feature: F002 — TX FIFO Management
    Goal: Verify that writing to a full TX FIFO is handled correctly
          per the specification (data rejected, interrupt asserted,
          no corruption of existing FIFO contents).

    Procedure:
      1. Reset and configure for 8N1 at 115200 baud.
      2. Disable TX so FIFO does not drain.
      3. Write FIFO_DEPTH bytes to fill the FIFO completely.
      4. Verify tx_full interrupt asserts.
      5. Attempt to write one more byte (overflow).
      6. Verify the overflow byte is rejected (FIFO level unchanged).
      7. Re-enable TX and verify all original bytes transmit correctly.

    Expected:
      - FIFO full interrupt asserts at capacity.
      - Overflow write does not corrupt existing data.
      - All originally queued bytes transmit without error.
    """
    await reset_dut(dut)
    await configure_uart(dut, baud=115200, data_bits=8, parity="none", stop_bits=1)
    await disable_tx(dut)

    fifo_depth = 16

    # Fill FIFO to capacity
    for i in range(fifo_depth):
        await write_csr(dut, SIGNALS["tx_data_reg"], i & 0xFF)

    # Verify full condition
    full_irq = await read_csr(dut, SIGNALS["tx_full_irq"])
    assert full_irq, "TX full interrupt should be asserted when FIFO is at capacity"

    # Attempt overflow
    await write_csr(dut, SIGNALS["tx_data_reg"], 0xAA)
    level = await read_csr(dut, SIGNALS["tx_fifo_lvl"])
    assert level == fifo_depth, "FIFO level should not exceed capacity on overflow"

    # Drain and verify data integrity
    await enable_tx(dut)
    for i in range(fifo_depth):
        tx_byte = await capture_tx_byte(dut)
        assert tx_byte == (i & 0xFF), \
            f"Data corruption: expected {i & 0xFF:#x}, got {tx_byte:#x}"


# ── Helper stubs ─────────────────────────────────────────────────────────────
# These helpers express verification intent. Actual implementation depends
# on the RTL interface and CSR map.

async def reset_dut(dut):
    """Assert reset for 10 clock cycles, then deassert."""
    raise NotImplementedError("Bind to actual reset sequence")

async def configure_uart(dut, baud, data_bits, parity, stop_bits):
    """Write UART configuration registers."""
    raise NotImplementedError("Bind to actual CSR addresses")

async def write_csr(dut, addr, data):
    """Perform a TL-UL write transaction to the given CSR address."""
    raise NotImplementedError("Bind to TL-UL bus agent")

async def read_csr(dut, addr):
    """Perform a TL-UL read transaction and return the data."""
    raise NotImplementedError("Bind to TL-UL bus agent")

async def wait_for_tx_complete(dut):
    """Wait until one byte has been fully transmitted on the serial line."""
    raise NotImplementedError("Bind to TX monitor")

async def disable_tx(dut):
    """Disable the TX module via control register."""
    raise NotImplementedError("Bind to TX enable control")

async def enable_tx(dut):
    """Enable the TX module via control register."""
    raise NotImplementedError("Bind to TX enable control")

async def capture_tx_byte(dut):
    """Capture and decode one byte from the serial TX output."""
    raise NotImplementedError("Bind to TX line monitor")
```

**Key principle:** These tests must be meaningful without RTL. A verification engineer reading them should understand exactly what is being tested, why, and what the expected behavior is. The `NotImplementedError` stubs are intentional -- they mark the boundary between specification-level intent and implementation-level detail.

### 3. Functional Coverage Model

A coverage model describing what **should** be covered by any correct verification campaign, independent of RTL implementation details.

```yaml
functional_coverage:
  dut_name: "nexus_uart"

  covergroups:
    - name: "cg_tx_configuration"
      description: "TX operating mode configuration coverage"
      sample_event: "On each TX frame transmission"
      coverpoints:
        - name: "cp_data_width"
          description: "Data bits per frame"
          bins:
            - { name: "5_bits", value: 5 }
            - { name: "6_bits", value: 6 }
            - { name: "7_bits", value: 7 }
            - { name: "8_bits", value: 8 }
        - name: "cp_parity"
          description: "Parity mode"
          bins:
            - { name: "none", value: 0 }
            - { name: "even", value: 1 }
            - { name: "odd", value: 2 }
        - name: "cp_stop_bits"
          description: "Number of stop bits"
          bins:
            - { name: "one", value: 1 }
            - { name: "two", value: 2 }
      crosses:
        - name: "cx_tx_mode"
          coverpoints: ["cp_data_width", "cp_parity", "cp_stop_bits"]
          description: "Cross-coverage of all TX configuration combinations"

    - name: "cg_tx_fifo"
      description: "TX FIFO state coverage"
      sample_event: "On each FIFO write or read"
      coverpoints:
        - name: "cp_fifo_level"
          description: "FIFO occupancy at time of operation"
          bins:
            - { name: "empty", value: 0 }
            - { name: "low", range: [1, 4] }
            - { name: "mid", range: [5, 11] }
            - { name: "high", range: [12, 15] }
            - { name: "full", value: 16 }
        - name: "cp_fifo_operation"
          description: "Type of FIFO access"
          bins:
            - { name: "write", value: "write" }
            - { name: "read", value: "read" }
      crosses:
        - name: "cx_fifo_state_op"
          coverpoints: ["cp_fifo_level", "cp_fifo_operation"]
          description: "All FIFO levels observed during both write and read"

    - name: "cg_error_conditions"
      description: "Error scenario coverage"
      sample_event: "On error event detection"
      coverpoints:
        - name: "cp_error_type"
          description: "Types of error conditions exercised"
          bins:
            - { name: "parity_error", value: "parity" }
            - { name: "framing_error", value: "framing" }
            - { name: "rx_overflow", value: "rx_overflow" }
            - { name: "tx_overflow", value: "tx_overflow" }
            - { name: "break_condition", value: "break" }

    # ... additional covergroups for RX, interrupts, CSR access, etc.
```

### 4. Behavioral Assertions

Properties that any correct implementation of the specification must satisfy. These are expressed in a structured format that can later be translated into SVA, PSL, or Python-based checkers.

```yaml
assertions:
  dut_name: "nexus_uart"

  protocol_assertions:
    - id: "A001"
      name: "TX idle state"
      description: >
        The TX output line shall be held high (idle) when no transmission
        is in progress.
      type: safety
      severity: error
      feature_ref: "F001"
      pseudo_property: >
        always: (tx_state == IDLE) implies (tx_output == 1)

    - id: "A002"
      name: "TX start bit timing"
      description: >
        Each transmitted frame shall begin with exactly one bit-period
        of low level (start bit) before the first data bit.
      type: safety
      severity: error
      feature_ref: "F001"
      pseudo_property: >
        on(tx_frame_start):
          tx_output == 0 for exactly (clock_freq / baud_rate) cycles
          followed_by tx_data_phase

    - id: "A003"
      name: "TX data bit order"
      description: >
        Data bits shall be transmitted LSB first, matching the value
        written to the TX data register.
      type: safety
      severity: error
      feature_ref: "F001"
      pseudo_property: >
        on(tx_frame_start):
          for bit_idx in 0..data_bits-1:
            tx_output at (start_bit_end + bit_idx * bit_period)
              == tx_data_register[bit_idx]

    - id: "A004"
      name: "TX FIFO full flag accuracy"
      description: >
        The TX FIFO full status flag shall assert when the FIFO occupancy
        reaches its maximum capacity and deassert when occupancy drops
        below maximum.
      type: safety
      severity: error
      feature_ref: "F002"
      pseudo_property: >
        always: (fifo_count == FIFO_DEPTH) iff (fifo_full_flag == 1)

    - id: "A005"
      name: "No data loss in normal operation"
      description: >
        Every byte written to the TX FIFO when the FIFO is not full
        shall eventually appear on the TX output line, in order.
      type: liveness
      severity: error
      feature_ref: "F002"
      pseudo_property: >
        on(fifo_write when !fifo_full):
          eventually: written_data appears on tx_output in FIFO order

    - id: "A006"
      name: "RX parity error detection"
      description: >
        When parity checking is enabled and a received frame has incorrect
        parity, the parity_error status bit shall assert before the next
        frame begins.
      type: safety
      severity: error
      feature_ref: "F010"
      pseudo_property: >
        on(rx_frame_complete when parity_enabled):
          (computed_parity != received_parity) implies
            (parity_error_status == 1) before next(rx_frame_start)

  structural_assertions:
    - id: "A020"
      name: "Reset state"
      description: >
        Upon reset assertion, all control registers shall return to
        their documented reset values, FIFOs shall be empty, and
        TX output shall be idle (high).
      type: safety
      severity: error
      feature_ref: "F_RESET"
      pseudo_property: >
        on(reset_asserted):
          all_csrs == reset_values
          and fifo_count == 0
          and tx_output == 1

    - id: "A021"
      name: "Interrupt consistency"
      description: >
        An interrupt output shall assert if and only if at least one
        enabled interrupt source has its status bit set.
      type: safety
      severity: error
      feature_ref: "F_INTR"
      pseudo_property: >
        always: interrupt_output == |(interrupt_status & interrupt_enable)

  # ... additional assertions ...
```

---

## Entry Point

```bash
python run_spec_interpreter.py \
  --spec <path_to_spec.md> \
  --output_dir <path_to_output_directory>
```

| Flag | Description |
|------|-------------|
| `--spec` | Path to the natural-language specification (Markdown format) |
| `--output_dir` | Directory where all generated artifacts must be written |

**Note:** There is no `--rtl` or `--csr_map` flag. The agent receives only the specification.

---

## Required Output Structure

```
output_dir/
├── vplan.yaml              — Structured verification plan
├── tests/                  — Cocotb test stubs
│   ├── test_tx_basic.py
│   ├── test_tx_fifo.py
│   ├── test_rx_basic.py
│   ├── test_rx_errors.py
│   ├── test_interrupts.py
│   ├── test_csr_access.py
│   └── helpers.py          — Shared helper stubs
├── coverage/
│   └── coverage_model.yaml — Functional coverage model
├── assertions/
│   └── assertions.yaml     — Behavioral assertions
└── report.md               — Agent's reasoning and methodology
```

---

## Evaluation Specifications

Your agent will be evaluated on **2 unseen specifications** (not the competition DUT specs). These specifications:

- Describe hardware peripherals of comparable complexity to the competition DUTs
- Are written in the same format and level of detail as the provided competition specs
- Cover a mix of protocol-based (with external interfaces) and register-based (CSR-only) designs

A panel of **3 expert verification engineers** will independently evaluate each submission against a reference verification plan that they produced from the same specification. Scores are averaged across judges.

---

## Evaluation Rubric

### Automated Scoring (20% -- 80 points)

| Category | Points | Criteria |
|----------|--------|----------|
| **Output Structure** | 30 pts | All required files present in the correct directory structure. Correct file naming. No missing top-level artifacts. |
| **YAML Syntax** | 25 pts | `vplan.yaml`, `coverage_model.yaml`, and `assertions.yaml` parse without errors. Schema-valid (required fields present, correct types). |
| **Python Syntax** | 25 pts | All test stub files are syntactically valid Python. Import statements resolve. No syntax errors. Test functions use `@cocotb.test()` decorator. |

### Judge Scoring (80% -- 320 points)

Scored per evaluation specification. Points listed below are per specification; final score is the average across both specifications, scaled to the 320-point budget.

| Category | Points (per spec) | Criteria |
|----------|-------------------|----------|
| **Verification Plan Completeness** | 0--100 pts | Does the plan cover all testable features in the specification? Are there gaps where the expert plan has features that the agent missed? Scored as a ratio: (agent features that match expert) / (total expert features). Bonus points for agent-identified features that the expert missed but are valid. |
| **Verification Plan Accuracy** | 0--100 pts | Are the feature descriptions correct? Are priority and risk assessments reasonable? Are test strategies appropriate for each feature? Are coverage goals meaningful and achievable? Penalized for hallucinated features (described in the plan but not in the specification). |
| **Coverage Model Quality** | 0--100 pts | Are the covergroups well-structured and meaningful? Do coverpoints correspond to real specification parameters? Are crosses used appropriately (not just exhaustive cross of everything)? Are bins well-chosen (boundary values, equivalence classes)? Does the model distinguish between what matters and what does not? |
| **Assertion Quality** | 0--100 pts | Do assertions capture real specification requirements? Are temporal relationships expressed correctly? Is the mix of safety vs. liveness properties appropriate? Are assertions specific enough to catch bugs but general enough to avoid false positives? Are critical protocol invariants covered? |

#### Judge Evaluation Guidelines

Judges will assess each category on the following scale:

| Score Range | Meaning |
|-------------|---------|
| 0--20 | Minimal effort. Major gaps. Mostly incorrect or irrelevant. |
| 21--40 | Partial coverage. Some correct elements but significant omissions or errors. |
| 41--60 | Adequate. Covers the main features but misses subtleties, edge cases, or has accuracy issues. |
| 61--80 | Good. Comprehensive coverage with minor gaps. Accurate and well-structured. |
| 81--100 | Excellent. Matches or exceeds expert quality. Insightful coverage of corner cases and non-obvious specification requirements. |

---

## Submission Format

```
submission/
  task_4_3/
    run_spec_interpreter.py     — Entry point
    requirements.txt            — Python dependencies
    agent/                      — Your agent source code
    config/                     — Configuration files (if any)
    README.md                   — Architecture overview
```

The platform will execute your agent in a sandboxed environment with:

- Python 3.11+
- Network access (for LLM API calls only)
- 16 GB RAM, 8 CPU cores
- 30-minute wall-clock limit per specification

---

## Tips for Success

1. **Read the specification like a verification engineer, not a designer.** Designers ask "how does it work?" Verification engineers ask "how can it break?" Your agent should identify failure modes, boundary conditions, and error scenarios -- not just happy-path behavior.

2. **Structure the vplan hierarchically.** Group features by functional block (TX, RX, FIFO, CSR, interrupts, errors). This makes the plan easier for judges to evaluate and demonstrates systematic thinking.

3. **Do not hallucinate features.** The biggest penalty risk is generating plausible-sounding features that are not in the specification. If the spec does not mention DMA, do not include a DMA coverage group. Judges will specifically check for fabricated content.

4. **Make assertions temporal.** Simple value-checking assertions (e.g., "output should be 1") are less valuable than temporal assertions that capture sequences of events ("after X happens, Y must follow within N cycles"). Focus on protocol-level properties that express the specification's behavioral requirements.

5. **Coverage crosses should be purposeful.** A full cross of every coverpoint with every other coverpoint creates an explosion of bins, most of which are meaningless. Choose crosses that represent real operational scenarios (e.g., crossing FIFO level with operation type is meaningful; crossing baud rate with interrupt type probably is not).

6. **Test stubs should tell a story.** Each test should have a clear docstring explaining: what feature it tests, what the setup is, what stimulus is applied, and what the expected outcome is. A judge should understand the test's purpose without reading any code below the docstring.

7. **Do not ignore the negative space.** Specifications often define what should NOT happen (no data corruption, no spurious interrupts, no response without request). These negative requirements are some of the most valuable assertions and coverage goals.
