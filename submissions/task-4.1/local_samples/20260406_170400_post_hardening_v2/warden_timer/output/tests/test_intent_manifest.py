# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_and_csr_map: Verify reset values for all implemented CSRs, basic TL-UL reads/writes, address decoding across the 64-byte window, and reserved-bit RAZ/WI behavior.
# - mtime_monotonic_and_prescaler_zero: Confirm mtime increments every clock when PRESCALER=0, remains monotonic, and low/high halves read consistently across rollover-sensitive sampling.
# - prescaler_basic_and_update_latency: Program a nonzero prescaler and verify mtime increments once per prescaler+1 cycles; change prescaler while active and confirm the new value takes effect only on the next boundary.
# - timer0_compare_interrupt_flow: Program MTIMECMP0 below/above current mtime, verify raw interrupt assertion, INTR_ENABLE masking, and W1C clearing through INTR_STATE.
# - timer1_compare_interrupt_flow: Repeat comparator interrupt validation for MTIMECMP1 to ensure both comparators operate independently.
# - 64bit_compare_partial_write_intermediate_state: Write comparator LOW then HIGH and HIGH then LOW around active mtime to observe intermediate compare behavior and confirm no atomicity is assumed.
# - intr_test_sets_state_and_output: Use INTR_TEST to inject each interrupt bit, verify INTR_STATE sets, output follows enable mask, and W1C clears each bit.
# - watchdog_enable_pet_bark_bite: Enable watchdog, verify count increments, pet resets count, bark threshold raises interrupt, and bite threshold asserts alert_o.
# - watchdog_lock_freezes_control_but_allows_pet: Set wd_lock, confirm WATCHDOG_CTRL cannot be cleared or modified except by reset, while WATCHDOG_PET remains functional.
# - reset_clears_lock_and_status: Assert hardware reset after lock/bark/bite activity and verify watchdog lock, counters, interrupt state, and alert return to reset defaults.
#
# Random tests:
# - tlul_csr_fuzz_smoke: Run constrained-random TL-UL reads/writes over the valid CSR window with scoreboard checking for legal register behavior, reserved-bit masking, and no bus protocol errors.
# - timer_watchdog_constrained_random: Randomize prescaler, comparator thresholds, watchdog thresholds, enable/mask/lock sequences, and periodic pet timing to explore mixed timer/watchdog interactions within a short run.
# - interrupt_state_random_sequence: Randomly exercise INTR_TEST, INTR_ENABLE, and W1C clearing sequences while checking that output pins reflect masked raw state correctly.
