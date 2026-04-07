# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_register_smoke: Verify reset values for all readable CSRs, confirm mtime and watchdog count start at zero, and validate TL-UL read/write access to the full register map.
# - mtime_prescaler_basic: Program prescaler values 0, 1, and a mid-range value to confirm mtime increments at the expected rate and remains monotonic.
# - timer0_compare_interrupt: Program mtimecmp0 below and above current mtime, enable intr_o[0], and verify interrupt assertion, W1C clearing, and re-assertion behavior.
# - timer1_compare_interrupt: Repeat comparator validation for mtimecmp1, including INTR_TEST injection and INTR_STATE clearing.
# - 64bit_compare_partial_write: Write comparator LOW and HIGH halves in both orders to validate intermediate compare states and ensure no atomic-write assumption is required.
# - watchdog_enable_pet_bark_bite: Enable watchdog, set bark and bite thresholds, observe watchdog_count progression, verify bark interrupt, pet reset, and bite alert assertion.
# - watchdog_lock_behavior: Set wd_lock, attempt to clear or modify watchdog control fields, confirm lock persistence until reset, and verify WATCHDOG_PET remains writable.
# - interrupt_masking_and_test: Exercise INTR_ENABLE masking, INTR_TEST self-triggering, and confirm output pins only assert when both state and enable are set.
# - reserved_bits_and_ro_wo_access: Write reserved bits in PRESCALER and WATCHDOG_CTRL, attempt writes to RO registers, and confirm readback/side-effect behavior is compliant.
#
# Random tests:
# - tlul_csr_fuzz_sanity: Run constrained-random TL-UL reads/writes across the 64-byte window with scoreboard checking for legal CSR behavior, focusing on accessible registers and expected read-only/write-only responses.
# - timer_watchdog_constrained_random: Randomize prescaler, comparator thresholds, watchdog thresholds, enable/mask settings, and pet timing to stress concurrent timer and watchdog interactions.
# - interrupt_state_random_sequence: Randomly toggle INTR_ENABLE, inject INTR_TEST, and clear INTR_STATE while checking that interrupt outputs track the logical AND of state and enable.
