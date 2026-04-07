# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_and_csr_map: Verify reset values for all visible CSRs, confirm TL-UL reads/writes to each implemented register, and check that mtime and watchdog count start at zero with interrupts and alert deasserted.
# - mtime_prescaler_basic: Program prescaler values 0, 1, and a mid-range value to confirm mtime increments at the expected rate and remains monotonic across prescaler changes.
# - timer0_compare_interrupt: Program MTIMECMP0 below and above current mtime, enable intr_o[0], and verify raw interrupt, masked output, and W1C clear behavior.
# - timer1_compare_interrupt: Repeat comparator validation for MTIMECMP1, including independent operation from timer0 and correct interrupt enable masking.
# - comparator_partial_write_ordering: Write LOW then HIGH and HIGH then LOW for 64-bit comparator programming while mtime is active, checking intermediate compare behavior and final threshold correctness.
# - intr_test_and_w1c: Use INTR_TEST to force each interrupt bit, confirm INTR_STATE sets, verify output gating through INTR_ENABLE, and clear each bit with W1C writes.
# - watchdog_enable_bark_bite: Enable watchdog, program bark and bite thresholds, observe bark interrupt before bite alert, and confirm alert_o asserts at bite threshold.
# - watchdog_pet_resets_counter: Pet the watchdog before bark threshold and verify the counter returns to zero and no bark or bite occurs.
# - watchdog_lock_behavior: Set wd_lock, attempt to clear lock and modify watchdog control fields, verify lock is sticky until reset, and confirm WATCHDOG_PET remains writable.
# - reserved_bits_and_access_policy: Write non-zero values to reserved bits and read back to confirm RAZ/WI behavior; also attempt reads from WO register and writes to RO register to ensure no unintended side effects.
#
# Random tests:
# - tlul_csr_fuzz_with_scoreboard: Run constrained-random TL-UL reads/writes across the 64-byte window with a mirrored CSR model, checking access permissions, reset defaults, and reserved-bit behavior.
# - timer_watchdog_concurrent_stress: Randomize prescaler, comparator thresholds, watchdog thresholds, enable masks, and pet timing while continuously checking mtime monotonicity, interrupt correctness, and alert generation.
# - partial_64bit_programming_fuzz: Randomize the order and spacing of LOW/HIGH writes for both comparators to expose transient compare hazards and ensure final programmed values are honored.
# - interrupt_masking_and_clear_stress: Randomly toggle INTR_ENABLE and issue W1C clears while interrupts are pending to validate output gating and state retention semantics.
