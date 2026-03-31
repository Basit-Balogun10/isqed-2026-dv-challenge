# Task 1.4: Assertion Library

**Phase 1 | 350 points per DUT | Up to 2 DUTs | Max 700 points**

---

## Overview

Generate a comprehensive SystemVerilog Assertion (SVA) library for your chosen DUTs. The library must include protocol-level, functional, structural, and liveness assertions that continuously monitor the DUT during simulation. Assertions must be correct on clean RTL (no false positives) and effective at catching bugs in mutant RTL (high detection rate).

This task evaluates your ability to express specification requirements as formal temporal properties -- one of the most impactful verification activities and one where AI-assisted generation shows both high promise and significant pitfalls.

---

## Available DUTs

| Tier | DUT Name | Protocol | Approx. Lines | Assertion Complexity |
|------|----------|----------|---------------|---------------------|
| Tier 1 (Starter) | `nexus_uart` | UART | ~500 | Moderate |
| Tier 1 (Starter) | `bastion_gpio` | GPIO | ~400 | Low-Moderate |
| Tier 2 (Intermediate) | `warden_timer` | Timer/Watchdog | ~600 | Moderate |
| Tier 2 (Intermediate) | `citadel_spi` | SPI Host | ~900 | High |
| Tier 3 (Advanced) | `aegis_aes` | AES-128 | ~1200 | High |
| Tier 3 (Advanced) | `sentinel_hmac` | HMAC-SHA256 | ~1000 | High |
| Tier 4 (Expert) | `rampart_i2c` | I2C Host/Target | ~1100 | Very High |

All DUTs share a common **TileLink-UL simplified bus interface** (`tl_i`/`tl_o` with ready/valid handshake), active-low asynchronous reset (`rst_ni`), and standard interrupt (`intr_o`) and alert (`alert_o`) outputs.

You may submit assertion libraries for **up to 2 DUTs**. A minimum of **20 assertions per DUT** is required for full score consideration.

---

## Assertion Categories

Your library must include assertions from each of the following four categories:

### 1. Protocol Assertions

Verify that the DUT's external interfaces comply with their respective protocol specifications.

**TL-UL bus protocol (applicable to all DUTs):**

```systemverilog
// A-channel valid must not be deasserted without a ready handshake
property tl_a_valid_stability;
  @(posedge clk_i) disable iff (!rst_ni)
  (tl_i.a_valid && !tl_o.a_ready) |=> tl_i.a_valid;
endproperty
assert_tl_a_valid_stable: assert property (tl_a_valid_stability)
  else $error("TL-UL violation: a_valid dropped without handshake");

// D-channel must respond within a bounded number of cycles
property tl_d_response_bound;
  @(posedge clk_i) disable iff (!rst_ni)
  (tl_i.a_valid && tl_o.a_ready) |-> ##[1:128] (tl_o.d_valid && tl_i.d_ready);
endproperty
assert_tl_d_response: assert property (tl_d_response_bound)
  else $error("TL-UL violation: no D-channel response within 128 cycles");
```

**DUT-specific protocol (examples):**

- **UART:** Start bit is always low; stop bit is always high; frame length matches configured data bits + parity.
- **SPI:** SCLK only toggles while CS is asserted; data transitions occur on the correct clock edge for the configured CPOL/CPHA mode.
- **I2C:** SDA only changes while SCL is low (except START/STOP conditions); ACK/NACK appears at the 9th clock of each byte.

### 2. Functional Assertions

Verify that the DUT's behavior matches its specification under normal operating conditions.

**Example -- `warden_timer` countdown assertion:**

```systemverilog
// When enabled with prescale=0, counter must increment by 'step' each cycle
property timer_count_increment;
  int unsigned prev_count;
  @(posedge clk_i) disable iff (!rst_ni)
  (ctrl_reg.enable && ctrl_reg.prescale == 0,
   prev_count = counter_reg) |=>
  (counter_reg == prev_count + ctrl_reg.step);
endproperty
assert_timer_increment: assert property (timer_count_increment)
  else $error("Timer: counter did not increment by step=%0d", ctrl_reg.step);
```

**Example -- `aegis_aes` output validity:**

```systemverilog
// After start is triggered, output valid must assert within max latency
property aes_output_latency;
  @(posedge clk_i) disable iff (!rst_ni)
  (ctrl_reg.start && !status_reg.busy) |-> ##[1:50] status_reg.output_valid;
endproperty
assert_aes_latency: assert property (aes_output_latency)
  else $error("AES: output_valid not asserted within 50 cycles of start");
```

### 3. Structural Assertions

Verify invariants that must always hold, regardless of the DUT's operational mode.

**Example -- `nexus_uart` FIFO never overflows:**

```systemverilog
// TX FIFO depth must never exceed its configured maximum
assert_tx_fifo_no_overflow: assert property (
  @(posedge clk_i) disable iff (!rst_ni)
  (tx_fifo_depth <= TX_FIFO_MAX_DEPTH)
) else $error("UART: TX FIFO overflow detected (depth=%0d)", tx_fifo_depth);

// Interrupt state bits must be a subset of interrupt enable bits for output assertion
assert_intr_output_gated: assert property (
  @(posedge clk_i) disable iff (!rst_ni)
  (intr_o == |(intr_state_reg & intr_enable_reg))
) else $error("Interrupt output does not match (state & enable)");
```

### 4. Liveness Assertions

Verify that the DUT makes forward progress and does not deadlock or hang.

**Example -- `citadel_spi` transaction completion:**

```systemverilog
// Once a SPI transaction starts, it must complete within a bounded time
property spi_transaction_liveness;
  @(posedge clk_i) disable iff (!rst_ni)
  (ctrl_reg.start && !status_reg.busy) |->
    s_eventually (status_reg.idle);
endproperty
assert_spi_liveness: assert property (spi_transaction_liveness)
  else $error("SPI: transaction did not complete -- possible deadlock");

// After reset, DUT must reach idle state
property reset_to_idle;
  @(posedge clk_i)
  ($rose(rst_ni)) |-> ##[1:16] (status_reg.idle);
endproperty
assert_reset_idle: assert property (reset_to_idle)
  else $error("DUT did not reach idle within 16 cycles after reset");
```

---

## Assertion Binding and Organization

Assertions should be organized in a bind module so they can be attached to the DUT without modifying the RTL:

```systemverilog
module nexus_uart_assertions (
  input logic        clk_i,
  input logic        rst_ni,
  input tl_ul_pkg::tl_h2d_t tl_i,
  input tl_ul_pkg::tl_d2h_t tl_o,
  input logic        tx_o,
  input logic        rx_i,
  input logic        intr_tx_watermark_o,
  input logic        intr_rx_watermark_o,
  // ... all relevant internal signals
);

  // === Protocol Assertions ===
  // ...

  // === Functional Assertions ===
  // ...

  // === Structural Assertions ===
  // ...

  // === Liveness Assertions ===
  // ...

endmodule

// Bind to the DUT
bind nexus_uart nexus_uart_assertions u_assertions (
  .clk_i              (clk_i),
  .rst_ni             (rst_ni),
  .tl_i               (tl_i),
  .tl_o               (tl_o),
  .tx_o               (tx_o),
  .rx_i               (rx_i),
  .intr_tx_watermark_o(intr_tx_watermark_o),
  .intr_rx_watermark_o(intr_rx_watermark_o)
  // ...
);
```

---

## Submission Format

```
submission/
  task_1_4/
    <dut_name>/
      assertions/
        <dut>_protocol_assertions.sv    # Protocol compliance checks
        <dut>_functional_assertions.sv  # Behavioral correctness checks
        <dut>_structural_assertions.sv  # Invariant checks
        <dut>_liveness_assertions.sv    # Forward progress checks
      bind/
        <dut>_assertion_bind.sv         # Bind module
      docs/
        assertion_manifest.csv          # ID, category, description, severity
      filelist.f                        # Compilation file list
```

The `assertion_manifest.csv` must list every assertion with its ID, category, one-line description, and severity level:

```csv
id,category,description,severity
UART_PROTO_001,protocol,TX start bit must be low,error
UART_PROTO_002,protocol,TX stop bit must be high,error
UART_FUNC_001,functional,TX FIFO drains in order,error
UART_STRUCT_001,structural,TX FIFO depth within bounds,error
UART_LIVE_001,liveness,TX byte completes within frame period,error
...
```

---

## Evaluation Rubric

### Automated Scoring (85% -- 297.5 points per DUT)

| Category | Points | Criteria |
|----------|--------|----------|
| **No False Positives** | _Gate_ | **All assertions must pass on clean reference RTL** under a standard test suite. Any assertion that fires on correct RTL is disqualified and not counted. This is a hard gate, not a point category. |
| **Bug Detection** | ~10 pts per bug | Assertions are evaluated against a hidden set of **injected bugs** in the RTL. For each bug that triggers at least one assertion, 10 pts are awarded. The bug set includes functional errors, protocol violations, and corner-case issues. Total available depends on DUT complexity (typically 15-25 bugs per DUT). Points scaled to fit the budget. |
| **Mutant Detection** | ~5 pts per mutant | Assertions are evaluated against **automatically generated mutants** (operator replacements, signal inversions, constant substitutions). For each mutant killed by at least one assertion, 5 pts are awarded. Total available depends on DUT size (typically 20-40 mutants per DUT). Points scaled to fit the budget. |

_Scaling: Bug detection and mutant detection raw scores are summed and scaled so that catching all bugs and all mutants yields the full 297.5 automated points._

### Judge Scoring (15% -- 52.5 points per DUT)

| Category | Points | Criteria |
|----------|--------|----------|
| **Assertion Quality** | 20 pts | Assertions are well-scoped (one property per assertion), use proper disable conditions, avoid vacuous passes, and handle edge cases (reset, back-to-back transactions, boundary values). |
| **Temporal Sophistication** | 15 pts | Effective use of SVA temporal operators: implication (`|->`), sequences (`##`), repetition (`[*N]`, `[->N]`), `throughout`, `within`, `$rose`/`$fell`, `$past`. Assertions go beyond simple combinational checks to express meaningful multi-cycle properties. |
| **Specification Coverage** | 17.5 pts | Assertions collectively cover the DUT's full specification: all operating modes, error conditions, interrupt behavior, and protocol edge cases. Assessed by comparing assertion intent against the DUT specification. |

---

## Key Challenge

AI-generated assertions are notorious for two failure modes:

1. **Syntax and semantic errors.** Incorrect use of SVA operators, missing clock/reset contexts, type mismatches, and signal name errors cause compilation failures. An assertion that does not compile earns zero points.

2. **Incorrect temporal semantics.** An assertion that looks plausible but expresses the wrong property can be worse than no assertion at all -- it may pass on buggy RTL (false negative) or fail on correct RTL (false positive, disqualification).

The winning approach involves an **iterative compile-check-fix loop**:

```
1. Generate assertion candidates from the specification
2. Compile against the DUT RTL
3. Fix any compilation errors
4. Run on clean RTL to check for false positives
5. Remove or fix any assertions that fire incorrectly
6. Repeat until all assertions compile and pass on clean RTL
```

Teams that submit assertions without running this loop will almost certainly lose points to the false-positive gate.

---

## Tips for AI-Assisted Development

1. **Read the RTL signal names exactly.** Assertion binding requires precise signal name matching. Extract the DUT's port list and internal signal names from the RTL before writing any assertions.

2. **Start with the easy wins.** TL-UL protocol assertions are reusable across all DUTs and follow well-documented rules. Protocol assertions for UART and SPI are also well-specified. Write these first.

3. **Use the specification as your oracle.** Every assertion should trace back to a specific sentence or requirement in the DUT specification. If you cannot point to a spec clause, the assertion may be wrong.

4. **Test with waveforms.** When an assertion fires unexpectedly, dump a waveform and inspect the failing cycle. This is the fastest way to determine whether the assertion is wrong or the RTL has a genuine issue.

5. **Avoid overly strict timing.** Assertions that require exact cycle counts (e.g., "output must appear exactly 3 cycles after input") are fragile. Prefer bounded ranges (`##[1:5]`) unless the specification mandates exact timing.

6. **Liveness assertions need care.** `s_eventually` and similar unbounded liveness properties can be difficult for simulation-based checking. Consider using bounded liveness (`##[1:MAX_LATENCY]`) for simulation and noting that the unbounded version would be appropriate for formal verification.

7. **Organize by category.** The manifest CSV is scored, and judges will assess coverage across all four categories. Ensure you have assertions in each category, not just functional checks.
