# Verification Plan

## Features
- TL-UL CSR access for 32-bit GPIO controller register map
- Reset behavior for all CSRs, outputs, interrupt state, and alert output
- Per-pin direction control via DIR affecting gpio_oe_o and gpio_o drive behavior
- DATA_OUT read/write behavior and observable propagation to gpio_o for output-enabled pins
- DATA_IN visibility of synchronized gpio_i values with expected two-cycle latency
- Two-stage input synchronizer behavior under stable transitions and short pulses
- Per-pin interrupt generation for rising-edge, falling-edge, level-high, and level-low modes
- INTR_STATE latch, W1C clear semantics, and re-assertion for active level interrupts
- INTR_ENABLE gating of intr_o relative to INTR_STATE
- INTR_TEST software injection path setting INTR_STATE without external pin stimulus
- Masked write behavior through MASKED_OUT_LOWER and MASKED_OUT_UPPER with atomic per-bit updates
- Readback behavior of masked write CSRs with lower 16-bit data and upper 16-bit zero
- Simultaneous multi-pin activity and interrupt vector behavior across multiple enabled pins
- Basic invalid/unsupported access robustness on TL-UL interface within practical smoke scope
- Alert output quiescent behavior during normal legal operation

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_defaults_smoke: After asynchronous active-low reset, verify key CSRs read default zero or benign values, gpio_o and gpio_oe_o are inactive, intr_o is clear, and alert_o remains deasserted.
- tlul_csr_rw_smoke: Perform basic TL-UL reads and writes across all discovered RW/W1C CSRs, confirming addressability, readback, and no unexpected bus errors during legal accesses.
- dir_and_output_drive_basic: Program DIR and DATA_OUT with walking patterns and verify gpio_oe_o mirrors DIR while gpio_o reflects DATA_OUT on output-enabled pins.
- data_in_two_cycle_sync: Toggle gpio_i pins while configured as inputs and verify DATA_IN updates only after the expected two-clock synchronizer latency.
- sync_glitch_filter_smoke: Apply sub-cycle and single-cycle pulses on gpio_i and check that very narrow pulses are not falsely guaranteed in DATA_IN while stable pulses of sufficient width are captured.
- intr_rising_edge_basic: Enable rising-edge interrupt on selected pins, drive 0-to-1 transitions, verify INTR_STATE latches, and confirm intr_o follows INTR_STATE & INTR_ENABLE.
- intr_falling_edge_basic: Enable falling-edge interrupt on selected pins, drive 1-to-0 transitions, and verify correct interrupt latching and output behavior.
- intr_level_high_basic: Enable level-high interrupt, hold synchronized input high, verify INTR_STATE assertion, W1C clear, and re-assertion while the level condition persists.
- intr_level_low_basic: Enable level-low interrupt, hold synchronized input low, verify INTR_STATE assertion, W1C clear, and re-assertion while the level condition persists.
- intr_enable_gating: Show that interrupt events set INTR_STATE regardless of INTR_ENABLE, while intr_o only asserts for enabled bits.
- intr_test_injection: Write INTR_TEST bits to inject interrupts, verify INTR_STATE sets without gpio_i activity, and confirm normal clear behavior through INTR_STATE W1C.
- intr_state_w1c_semantics: Preload multiple interrupt bits, clear selected bits with W1C patterns, and verify only written 1 bits clear while 0 bits remain unchanged.
- masked_out_lower_atomic: Exercise MASKED_OUT_LOWER with mixed mask/data patterns and verify only selected DATA_OUT[15:0] bits update atomically.
- masked_out_upper_atomic: Exercise MASKED_OUT_UPPER with mixed mask/data patterns and verify only selected DATA_OUT[31:16] bits update atomically.
- masked_out_readback: Read MASKED_OUT_LOWER and MASKED_OUT_UPPER after DATA_OUT programming and verify lower 16-bit data mirrors the corresponding half of DATA_OUT while upper 16 bits read zero.
- multi_pin_parallel_interrupts: Stimulate several pins in the same cycle with mixed enabled modes and verify all expected INTR_STATE bits and intr_o bits assert together within practical scoreboard expectations.
- output_input_independence_smoke: Mix input and output pins in the same transaction sequence to verify output programming does not corrupt synchronized input observation on unrelated pins.
- alert_quiescent_smoke: Run representative legal CSR and GPIO activity and verify alert_o stays inactive in the absence of protocol or integrity faults.

## Random Tests
- csr_random_access_regression: Randomize legal TL-UL CSR reads/writes, including RW, RO, and W1C handling, with a lightweight reference model to maximize register and branch coverage within the time budget.
- gpio_pin_mode_random: Randomize DIR, DATA_OUT, and gpio_i activity across all 32 pins, checking gpio_o, gpio_oe_o, and DATA_IN consistency against a cocotb model.
- interrupt_mode_mix_random: Randomly enable combinations of rising, falling, level-high, and level-low modes per pin with randomized input transitions to stress interrupt state generation and gating.
- masked_write_random: Randomize MASKED_OUT_LOWER and MASKED_OUT_UPPER writes interleaved with DATA_OUT reads to validate atomic bit updates and readback behavior over many patterns.
- w1c_and_reassert_random: Randomly clear interrupt bits while level conditions remain active or edge events recur, verifying correct W1C semantics and re-assertion behavior.
- multi_pin_burst_activity_random: Generate concurrent transitions on many gpio_i pins over short bursts to expose any priority or loss behavior hinted in the spec while checking for deterministic expected minimum behavior.
- tlul_backpressure_smoke_random: Apply randomized TL-UL ready/valid backpressure in a constrained smoke test to ensure CSR accesses remain functionally correct under simple handshake variation.

## Risk Areas
- Input synchronizer latency and sampling semantics (high): DATA_IN and edge detection operate on synchronized inputs with a stated two-cycle latency, making off-by-one-cycle bugs likely and high impact to both data and interrupts.
- Interrupt generation across mixed edge and level modes (high): Per-pin support for four simultaneous trigger types plus INTR_ENABLE gating creates many state combinations and a high chance of incorrect latching or masking.
- W1C clear and level interrupt re-assertion (high): The spec explicitly requires level interrupts to re-assert after clear if the condition persists, a common corner case that is easy to implement incorrectly.
- Masked write atomic update behavior (high): MASKED_OUT_LOWER and MASKED_OUT_UPPER use packed mask/data semantics that are error-prone in decode and bit indexing, with direct software-visible impact.
- Simultaneous multi-pin edge capture (medium): The spec hints at possible priority behavior under high activity, so concurrent transitions may reveal dropped or mis-ordered interrupt state updates.
- Direction transition behavior (medium): Ordering between DIR changes and data path updates is implementation-dependent, so tests must avoid over-constraining while still checking for gross inconsistencies.
- TL-UL protocol handling under backpressure (medium): Bus correctness is foundational, but within a 60-minute budget only smoke-level handshake variation is practical unless failures are observed.
- Glitch filtering expectations (medium): The spec does not guarantee exact minimum pulse capture width, so verification must be careful not to assert behavior beyond stable synchronizer expectations.
- Alert output behavior (low): alert_o is present but not functionally described beyond existence, so only quiescent checking is justified for this budget-limited plan.
- Undefined collisions between masked writes and related CSR writes (low): The spec marks simultaneous masked and direct writes as not fully specified, so autonomous tests should avoid treating such collisions as pass/fail criteria.
