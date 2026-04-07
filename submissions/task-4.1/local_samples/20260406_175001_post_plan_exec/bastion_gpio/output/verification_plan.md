# Verification Plan

## Features
- TL-UL CSR read/write access with basic protocol sanity
- 32-bit GPIO direction control via DIR register
- DATA_OUT drive behavior and gpio_oe_o gating
- Two-stage input synchronization visibility through DATA_IN
- Rising-edge and falling-edge interrupt detection
- Level-high and level-low interrupt behavior
- INTR_STATE W1C clear semantics
- INTR_ENABLE gating of intr_o outputs
- INTR_TEST software interrupt injection
- Masked write atomic update behavior for lower and upper halves
- Reset behavior for CSRs and outputs
- Per-pin independence across a representative subset and full-width smoke
- Concurrent bus access and back-to-back CSR sequencing
- Alert output smoke check
- Register map decode sanity for 12 CSRs

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_and_csr_map: Apply reset, verify TL-UL access is responsive, confirm readable/writable CSRs decode correctly, and check default values for DATA_IN, DATA_OUT, DIR, interrupt registers, and alert_o idle state.
- dir_and_output_drive_basic: Program selected pins as outputs, write DATA_OUT patterns, and verify gpio_o and gpio_oe_o reflect DIR and DATA_OUT for representative bits across lower and upper halves.
- input_sync_latency: Toggle gpio_i on a few pins and confirm DATA_IN updates only after the expected two-clock-cycle synchronization latency.
- rising_falling_interrupts: Enable rising and falling edge interrupts on selected pins, drive synchronized transitions, verify INTR_STATE latching and intr_o assertion only when INTR_ENABLE is set.
- level_interrupt_reassertion: Enable level-high and level-low modes, clear INTR_STATE while the level condition remains true, and verify the interrupt reasserts as specified.
- intr_test_injection: Write INTR_TEST with single-bit and multi-bit patterns, confirm corresponding INTR_STATE bits set without external gpio_i stimulus, and verify W1C clear behavior afterward.
- masked_write_lower_half: Exercise MASKED_OUT_LOWER with partial masks to update only selected bits in DATA_OUT[15:0], then read back and confirm unchanged bits retain prior values.
- masked_write_upper_half: Exercise MASKED_OUT_UPPER with partial masks to update only selected bits in DATA_OUT[31:16], then read back and confirm lower 16 bits of the read data mirror the upper-half output state.
- w1c_intr_state_clear: Set interrupt state via INTR_TEST and edge/level events, clear individual bits and multi-bit groups using W1C writes, and verify only targeted bits clear.
- mixed_direction_and_data_stability: Switch a subset of pins between input and output while applying DATA_OUT writes, checking that gpio_oe_o and observable outputs remain coherent and no bus errors occur.

## Random Tests
- constrained_csr_fuzzer: Run short randomized TL-UL CSR sequences over the 12-register map with legal accesses only, mixing reads, writes, W1C clears, and readbacks to catch decode and side-effect issues.
- gpio_activity_stress_subset: Randomly toggle a representative subset of gpio_i pins with varied pulse widths and phase relationships to stress synchronizer, edge detection, and interrupt latching within the time budget.
- masked_write_random_patterns: Generate random mask/data combinations for both masked output registers and compare readback against a software model of atomic bit updates.
- interrupt_mode_cross_product_sample: Randomly select pins and interrupt mode combinations across rising, falling, level-high, and level-low enables, then stimulate transitions to validate combined mode behavior.

## Risk Areas
- Interrupt generation and clearing semantics (high): Highest functional risk due to multiple trigger modes, W1C behavior, reassertion for level-sensitive interrupts, and dependence on synchronized inputs.
- Input synchronization and edge detection timing (high): Two-stage latency and edge detection on synchronized values are easy to implement incorrectly and can cause missed or spurious interrupts.
- Masked write atomicity and readback behavior (high): Masked writes are a key architectural feature and are prone to bit-lane or half-word decode bugs.
- DIR to gpio_o/gpio_oe_o mapping (medium): Core GPIO functionality must be correct for both input and output modes across all bits, especially at boundaries between lower and upper halves.
- TL-UL register decode and access permissions (medium): Basic bus integration risk is moderate; incorrect offsets, RO/RW/W1C behavior, or response handling would block all higher-level testing.
- Alert output behavior (low): alert_o is present but underspecified in the excerpt, so only smoke-level validation is practical within the budget.
