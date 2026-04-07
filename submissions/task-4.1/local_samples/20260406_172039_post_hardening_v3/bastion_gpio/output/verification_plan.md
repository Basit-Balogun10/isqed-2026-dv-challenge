# Verification Plan

## Features
- TL-UL CSR read/write access with basic protocol sanity
- 32-bit GPIO direction control via DIR register
- DATA_OUT driving and gpio_oe_o behavior for output pins
- DATA_IN synchronization latency and stable sampling behavior
- Per-pin interrupt enable and state handling
- Rising-edge interrupt detection
- Falling-edge interrupt detection
- Level-high interrupt behavior with re-assert after W1C clear
- Level-low interrupt behavior with re-assert after W1C clear
- Masked write atomic update behavior for lower and upper 16-bit halves
- INTR_TEST software-injected interrupt setting
- Reset behavior for CSRs and outputs
- Per-pin interrupt output reflection on intr_o
- Alert output idle-state observation

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_and_csr_map_sanity: Apply reset, verify TL-UL accessibility, confirm readable/writable CSRs at expected offsets, and check default-safe values for DATA_OUT, DIR, INTR_ENABLE, INTR_STATE, gpio_oe_o, intr_o, and alert_o.
- dir_output_drive_basic: Program a subset of pins as outputs, write DATA_OUT patterns, and verify gpio_o and gpio_oe_o reflect DIR and DATA_OUT for multiple bit positions including boundary pins 0, 15, 16, and 31.
- dir_input_tristate_basic: Program a subset of pins as inputs, drive gpio_i externally, and verify gpio_oe_o deasserts while DATA_IN eventually reflects synchronized input values after the expected latency.
- masked_write_lower_half: Exercise MASKED_OUT_LOWER with partial masks to confirm atomic update semantics on DATA_OUT[15:0] without disturbing unmasked bits.
- masked_write_upper_half: Exercise MASKED_OUT_UPPER with partial masks to confirm atomic update semantics on DATA_OUT[31:16] without disturbing unmasked bits.
- intr_test_sets_state: Write one-hot and multi-bit values to INTR_TEST and verify corresponding INTR_STATE bits set and intr_o follows INTR_STATE & INTR_ENABLE.
- rising_edge_interrupt: Configure a pin for input, enable rising-edge interrupt mode and INTR_ENABLE, toggle gpio_i low-to-high, and verify INTR_STATE and intr_o assert after synchronizer latency.
- falling_edge_interrupt: Configure a pin for input, enable falling-edge interrupt mode and INTR_ENABLE, toggle gpio_i high-to-low, and verify INTR_STATE and intr_o assert after synchronizer latency.
- level_high_interrupt_reassert: Enable level-high interrupt on a pin, drive gpio_i high, clear INTR_STATE with W1C, and verify the interrupt re-asserts while the level remains high.
- level_low_interrupt_reassert: Enable level-low interrupt on a pin, drive gpio_i low, clear INTR_STATE with W1C, and verify the interrupt re-asserts while the level remains low.
- multi_pin_interrupt_and_masking: Stimulate multiple pins with mixed edge and level modes to confirm per-pin independence, simultaneous interrupt behavior, and correct masking through INTR_ENABLE.
- w1c_clear_behavior: Set INTR_STATE via edge or INTR_TEST, clear selected bits using W1C writes, and verify only written-one bits clear while others remain set.

## Random Tests
- constrained_gpio_register_fuzz: Run short randomized TL-UL CSR sequences over DIR, DATA_OUT, INTR_ENABLE, INTR_STATE, INTR_TEST, and interrupt mode registers with a scoreboard model, using constrained legal accesses and a small number of seeds to fit the 60-minute budget.
- random_gpio_stimulus_with_interrupt_scoreboard: Randomly toggle gpio_i on a limited set of pins while randomly enabling edge/level modes and checking expected intr_o and INTR_STATE behavior with synchronizer-aware latency modeling.
- masked_write_randomized_patterns: Generate random mask/data combinations for MASKED_OUT_LOWER and MASKED_OUT_UPPER, compare against a reference model of DATA_OUT updates, and verify readback consistency.

## Risk Areas
- Input synchronizer latency and edge detection timing (high): The design uses a two-stage synchronizer and edge detection on synchronized values, so off-by-one-cycle expectations are a common source of false failures and real bugs.
- Interrupt re-assertion for level-sensitive modes after W1C clear (high): Level interrupts must reassert while the condition persists; this is a subtle state-machine behavior with high bug potential.
- Masked write atomicity and bit-lane mapping (high): Incorrect mask/data bit ordering or partial update behavior can silently corrupt outputs and is easy to miss without directed checks.
- Per-pin independence across 32 channels (medium): Boundary bits and mixed-mode operation can expose indexing errors, especially around pins 15/16 and 31.
- TL-UL CSR decode and register offset correctness (medium): A small CSR block can still have address decode or access-type issues; basic bus smoke plus a few negative checks are sufficient within budget.
- Alert output behavior (low): Only one alert output is present and the excerpt does not define functional triggers, so it is lower risk and should be observed for idle/stability rather than exhaustively tested.
