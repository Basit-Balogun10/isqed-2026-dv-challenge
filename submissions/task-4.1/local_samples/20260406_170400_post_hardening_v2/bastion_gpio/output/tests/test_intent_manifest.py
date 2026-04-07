# Auto-generated test intent summary
#
# Directed tests:
# - smoke_reset_and_idles: After reset, verify default CSR values where observable, gpio_oe_o deasserted or reset-consistent, gpio_o reset-consistent, intr_o cleared, alert_o inactive, and TL-UL reads complete cleanly.
# - csr_rw_basic_data_out_dir: Write/read DATA_OUT and DIR with several patterns and verify gpio_o follows DATA_OUT while gpio_oe_o follows DIR on a per-bit basis.
# - data_in_two_cycle_sync_latency: Toggle gpio_i pins and verify DATA_IN reflects synchronized values no earlier than two clocks later, using stable transitions and per-pin spot checks.
# - dir_input_output_transition: Exercise transitions between input and output modes while varying DATA_OUT and gpio_i, checking only architecturally guaranteed behavior and avoiding unspecified same-cycle ordering assumptions.
# - intr_rising_single_pin: Enable rising-edge interrupt for one pin, drive a low-to-high transition on gpio_i, verify INTR_STATE bit sets after synchronization latency and intr_o reflects INTR_ENABLE gating.
# - intr_falling_single_pin: Enable falling-edge interrupt for one pin, drive a high-to-low transition on gpio_i, verify INTR_STATE bit sets and intr_o behavior is correct.
# - intr_level_high_behavior: Enable level-high interrupt, hold synchronized input high, verify INTR_STATE asserts, W1C clear is temporary if level remains asserted, and intr_o remains/reasserts as specified.
# - intr_level_low_behavior: Enable level-low interrupt, hold synchronized input low, verify INTR_STATE asserts, W1C clear is temporary if level remains asserted, and intr_o remains/reasserts as specified.
# - intr_multiple_modes_same_pin: Enable multiple trigger modes on the same pin and verify combined behavior does not lose interrupt state or mis-gate intr_o.
# - intr_enable_gating: Verify INTR_STATE can set while INTR_ENABLE is 0 and intr_o remains low until INTR_ENABLE is asserted.
# - intr_state_w1c_semantics: Set multiple INTR_STATE bits, clear selected bits with W1C patterns, and verify only written 1 bits clear while 0 bits remain unchanged.
# - intr_test_injection: Write INTR_TEST bits to inject interrupts without gpio_i stimulus and verify INTR_STATE and intr_o update correctly.
# - masked_out_lower_atomic_update: Verify MASKED_OUT_LOWER updates only selected DATA_OUT[15:0] bits according to upper-half mask and readback returns lower-half value with upper-half zero.
# - masked_out_upper_atomic_update: Verify MASKED_OUT_UPPER updates only selected DATA_OUT[31:16] bits according to upper-half mask and readback returns upper-half value in low 16 bits with upper-half zero.
# - masked_write_preserves_unmasked_bits: Initialize DATA_OUT to known patterns, perform sparse masked writes on both halves, and verify unmasked bits are preserved exactly.
# - multi_pin_parallel_interrupts: Stimulate several pins with independent edge and level conditions in the same test and verify all expected INTR_STATE bits and intr_o bits are observed within practical limits.
# - tlul_csr_access_boundaries: Perform aligned reads/writes across all known CSR offsets and verify legal accesses respond correctly; include conservative probing of unmapped/partial excerpt registers only if discoverable from CSR metadata in testbench.
# - alert_stability_no_false_fire: During normal reset, CSR, GPIO, and interrupt activity, verify alert_o does not spuriously assert.
#
# Random tests:
# - rand_csr_gpio_regression: Constrained-random TL-UL read/write sequences across GPIO CSRs with a scoreboard for DATA_OUT, DIR, INTR_ENABLE, interrupt control registers, and masked write effects, excluding intentionally unspecified same-cycle collisions.
# - rand_gpio_input_activity: Randomly toggle gpio_i across multiple pins with controllable dwell times to cover synchronized DATA_IN updates, edge detection, and level interrupt behavior under moderate activity.
# - rand_interrupt_mix: Randomly configure per-pin rising, falling, level-high, and level-low enables plus INTR_ENABLE, then apply input stimulus and compare observed INTR_STATE/intr_o against a lightweight reference model.
# - rand_masked_write_sequences: Generate random DATA_OUT initialization followed by random MASKED_OUT_LOWER and MASKED_OUT_UPPER writes to maximize mask density and sparse-mask corner coverage.
# - rand_reset_during_activity: Assert and release reset during ongoing CSR traffic and gpio_i activity to verify clean recovery, reset dominance, and absence of stuck interrupt/output state.
# - rand_multi_pin_concurrency: Drive concurrent transitions on many pins while random interrupt modes are enabled to expose possible priority or loss behavior noted in the spec, with checking focused on no unexpected corruption and broad event capture.
