# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_and_csr_map: Apply reset, verify TL-UL access is responsive, confirm readable/writable CSRs decode correctly, and check default values for DATA_IN, DATA_OUT, DIR, interrupt registers, and alert_o idle state.
# - dir_and_output_drive_basic: Program selected pins as outputs, write DATA_OUT patterns, and verify gpio_o and gpio_oe_o reflect DIR and DATA_OUT for representative bits across lower and upper halves.
# - input_sync_latency: Toggle gpio_i on a few pins and confirm DATA_IN updates only after the expected two-clock-cycle synchronization latency.
# - rising_falling_interrupts: Enable rising and falling edge interrupts on selected pins, drive synchronized transitions, verify INTR_STATE latching and intr_o assertion only when INTR_ENABLE is set.
# - level_interrupt_reassertion: Enable level-high and level-low modes, clear INTR_STATE while the level condition remains true, and verify the interrupt reasserts as specified.
# - intr_test_injection: Write INTR_TEST with single-bit and multi-bit patterns, confirm corresponding INTR_STATE bits set without external gpio_i stimulus, and verify W1C clear behavior afterward.
# - masked_write_lower_half: Exercise MASKED_OUT_LOWER with partial masks to update only selected bits in DATA_OUT[15:0], then read back and confirm unchanged bits retain prior values.
# - masked_write_upper_half: Exercise MASKED_OUT_UPPER with partial masks to update only selected bits in DATA_OUT[31:16], then read back and confirm lower 16 bits of the read data mirror the upper-half output state.
# - w1c_intr_state_clear: Set interrupt state via INTR_TEST and edge/level events, clear individual bits and multi-bit groups using W1C writes, and verify only targeted bits clear.
# - mixed_direction_and_data_stability: Switch a subset of pins between input and output while applying DATA_OUT writes, checking that gpio_oe_o and observable outputs remain coherent and no bus errors occur.
#
# Random tests:
# - constrained_csr_fuzzer: Run short randomized TL-UL CSR sequences over the 12-register map with legal accesses only, mixing reads, writes, W1C clears, and readbacks to catch decode and side-effect issues.
# - gpio_activity_stress_subset: Randomly toggle a representative subset of gpio_i pins with varied pulse widths and phase relationships to stress synchronizer, edge detection, and interrupt latching within the time budget.
# - masked_write_random_patterns: Generate random mask/data combinations for both masked output registers and compare readback against a software model of atomic bit updates.
# - interrupt_mode_cross_product_sample: Randomly select pins and interrupt mode combinations across rising, falling, level-high, and level-low enables, then stimulate transitions to validate combined mode behavior.
