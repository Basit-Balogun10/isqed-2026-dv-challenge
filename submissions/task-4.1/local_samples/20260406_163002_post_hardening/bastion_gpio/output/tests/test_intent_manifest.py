# Auto-generated test intent summary
#
# Directed tests:
# - reset_defaults_smoke: After asynchronous active-low reset, verify key CSRs read default zero or benign values, gpio_o and gpio_oe_o are inactive, intr_o is clear, and alert_o remains deasserted.
# - tlul_csr_rw_smoke: Perform basic TL-UL reads and writes across all discovered RW/W1C CSRs, confirming addressability, readback, and no unexpected bus errors during legal accesses.
# - dir_and_output_drive_basic: Program DIR and DATA_OUT with walking patterns and verify gpio_oe_o mirrors DIR while gpio_o reflects DATA_OUT on output-enabled pins.
# - data_in_two_cycle_sync: Toggle gpio_i pins while configured as inputs and verify DATA_IN updates only after the expected two-clock synchronizer latency.
# - sync_glitch_filter_smoke: Apply sub-cycle and single-cycle pulses on gpio_i and check that very narrow pulses are not falsely guaranteed in DATA_IN while stable pulses of sufficient width are captured.
# - intr_rising_edge_basic: Enable rising-edge interrupt on selected pins, drive 0-to-1 transitions, verify INTR_STATE latches, and confirm intr_o follows INTR_STATE & INTR_ENABLE.
# - intr_falling_edge_basic: Enable falling-edge interrupt on selected pins, drive 1-to-0 transitions, and verify correct interrupt latching and output behavior.
# - intr_level_high_basic: Enable level-high interrupt, hold synchronized input high, verify INTR_STATE assertion, W1C clear, and re-assertion while the level condition persists.
# - intr_level_low_basic: Enable level-low interrupt, hold synchronized input low, verify INTR_STATE assertion, W1C clear, and re-assertion while the level condition persists.
# - intr_enable_gating: Show that interrupt events set INTR_STATE regardless of INTR_ENABLE, while intr_o only asserts for enabled bits.
# - intr_test_injection: Write INTR_TEST bits to inject interrupts, verify INTR_STATE sets without gpio_i activity, and confirm normal clear behavior through INTR_STATE W1C.
# - intr_state_w1c_semantics: Preload multiple interrupt bits, clear selected bits with W1C patterns, and verify only written 1 bits clear while 0 bits remain unchanged.
# - masked_out_lower_atomic: Exercise MASKED_OUT_LOWER with mixed mask/data patterns and verify only selected DATA_OUT[15:0] bits update atomically.
# - masked_out_upper_atomic: Exercise MASKED_OUT_UPPER with mixed mask/data patterns and verify only selected DATA_OUT[31:16] bits update atomically.
# - masked_out_readback: Read MASKED_OUT_LOWER and MASKED_OUT_UPPER after DATA_OUT programming and verify lower 16-bit data mirrors the corresponding half of DATA_OUT while upper 16 bits read zero.
# - multi_pin_parallel_interrupts: Stimulate several pins in the same cycle with mixed enabled modes and verify all expected INTR_STATE bits and intr_o bits assert together within practical scoreboard expectations.
# - output_input_independence_smoke: Mix input and output pins in the same transaction sequence to verify output programming does not corrupt synchronized input observation on unrelated pins.
# - alert_quiescent_smoke: Run representative legal CSR and GPIO activity and verify alert_o stays inactive in the absence of protocol or integrity faults.
#
# Random tests:
# - csr_random_access_regression: Randomize legal TL-UL CSR reads/writes, including RW, RO, and W1C handling, with a lightweight reference model to maximize register and branch coverage within the time budget.
# - gpio_pin_mode_random: Randomize DIR, DATA_OUT, and gpio_i activity across all 32 pins, checking gpio_o, gpio_oe_o, and DATA_IN consistency against a cocotb model.
# - interrupt_mode_mix_random: Randomly enable combinations of rising, falling, level-high, and level-low modes per pin with randomized input transitions to stress interrupt state generation and gating.
# - masked_write_random: Randomize MASKED_OUT_LOWER and MASKED_OUT_UPPER writes interleaved with DATA_OUT reads to validate atomic bit updates and readback behavior over many patterns.
# - w1c_and_reassert_random: Randomly clear interrupt bits while level conditions remain active or edge events recur, verifying correct W1C semantics and re-assertion behavior.
# - multi_pin_burst_activity_random: Generate concurrent transitions on many gpio_i pins over short bursts to expose any priority or loss behavior hinted in the spec while checking for deterministic expected minimum behavior.
# - tlul_backpressure_smoke_random: Apply randomized TL-UL ready/valid backpressure in a constrained smoke test to ensure CSR accesses remain functionally correct under simple handshake variation.
