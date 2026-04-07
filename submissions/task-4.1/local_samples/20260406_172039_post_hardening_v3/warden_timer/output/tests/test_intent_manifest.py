# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_sanity: Verify reset values, TL-UL accessibility, RO/WO/W1C semantics, and basic CSR map decoding for all 15 registers within the 64-byte window.
# - mtime_free_run_and_prescaler_basic: Confirm mtime starts at zero, increments monotonically, and advances at 1/(prescaler+1) rate for prescaler values 0, 1, and a mid-range value.
# - mtimecmp0_interrupt_basic: Program mtimecmp0 below and above current mtime, verify raw interrupt assertion, INTR_ENABLE masking, and W1C clearing through INTR_STATE.
# - mtimecmp1_interrupt_basic: Repeat comparator interrupt checks for mtimecmp1 to ensure both comparator channels operate independently.
# - partial_64bit_compare_write_order: Write comparator LOW then HIGH and HIGH then LOW while mtime is active to validate intermediate states and final compare behavior without atomic write assumptions.
# - interrupt_test_register: Use INTR_TEST to force each interrupt bit, confirm INTR_STATE sets, output pin follows INTR_ENABLE, and W1C clear works per bit.
# - watchdog_enable_bark_bite: Enable watchdog, set bark and bite thresholds, verify bark interrupt at threshold and alert_o at bite threshold, including persistence until pet/reset as specified.
# - watchdog_pet_and_count_reset: Write WATCHDOG_PET with arbitrary values to reset the watchdog counter and confirm counter restarts from zero while enabled.
# - watchdog_lock_and_reset_only_unlock: Set wd_lock, verify WATCHDOG_CTRL cannot be cleared by software, WATCHDOG_PET remains writable, and full reset restores unlock capability.
# - prescaler_change_on_boundary: Change PRESCALER while mtime is running and verify the new value takes effect on the next prescaler boundary without resetting the internal prescale phase.
#
# Random tests:
# - tlul_csr_fuzz_smoke: Run constrained-random TL-UL reads/writes across valid CSR addresses, checking protocol stability, register mirroring, and no unexpected bus errors within the 60-minute budget.
# - timer_watchdog_constrained_random: Randomize prescaler, comparator thresholds, watchdog thresholds, enable masks, and pet timing to explore mixed timer/watchdog interactions and interrupt/alert concurrency.
# - partial_write_order_randomized: Randomly choose LOW/HIGH write order for 64-bit comparator programming and verify final compare values and interrupt outcomes against a Python reference model.
# - interrupt_masking_random: Randomly toggle INTR_ENABLE while raw interrupt sources are active to validate masking behavior and W1C clearing under changing enable conditions.
