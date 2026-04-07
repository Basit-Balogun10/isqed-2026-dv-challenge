# Verification Plan

## Features
- TL-UL CSR read/write access with byte/word alignment checks
- 64-bit mtime free-running counter readback via LOW/HIGH registers
- 12-bit prescaler behavior including zero-prescale and delayed effect on update
- Two 64-bit timer comparators with interrupt generation and W1C clearing
- Interrupt enable masking and INTR_TEST software injection
- Watchdog enable, bark threshold, bite threshold, pet, and count readback
- Watchdog lock behavior preventing control changes until reset
- Alert output assertion on watchdog bite threshold
- Reset initialization and post-reset register defaults
- Reserved-bit read-as-zero and write-ignored behavior

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_and_csr_map: Verify reset values for all implemented CSRs, basic TL-UL reads/writes, address decoding across the 64-byte window, and reserved-bit RAZ/WI behavior.
- mtime_monotonic_and_prescaler_zero: Confirm mtime increments every clock when PRESCALER=0, remains monotonic, and low/high halves read consistently across rollover-sensitive sampling.
- prescaler_basic_and_update_latency: Program a nonzero prescaler and verify mtime increments once per prescaler+1 cycles; change prescaler while active and confirm the new value takes effect only on the next boundary.
- timer0_compare_interrupt_flow: Program MTIMECMP0 below/above current mtime, verify raw interrupt assertion, INTR_ENABLE masking, and W1C clearing through INTR_STATE.
- timer1_compare_interrupt_flow: Repeat comparator interrupt validation for MTIMECMP1 to ensure both comparators operate independently.
- 64bit_compare_partial_write_intermediate_state: Write comparator LOW then HIGH and HIGH then LOW around active mtime to observe intermediate compare behavior and confirm no atomicity is assumed.
- intr_test_sets_state_and_output: Use INTR_TEST to inject each interrupt bit, verify INTR_STATE sets, output follows enable mask, and W1C clears each bit.
- watchdog_enable_pet_bark_bite: Enable watchdog, verify count increments, pet resets count, bark threshold raises interrupt, and bite threshold asserts alert_o.
- watchdog_lock_freezes_control_but_allows_pet: Set wd_lock, confirm WATCHDOG_CTRL cannot be cleared or modified except by reset, while WATCHDOG_PET remains functional.
- reset_clears_lock_and_status: Assert hardware reset after lock/bark/bite activity and verify watchdog lock, counters, interrupt state, and alert return to reset defaults.

## Random Tests
- tlul_csr_fuzz_smoke: Run constrained-random TL-UL reads/writes over the valid CSR window with scoreboard checking for legal register behavior, reserved-bit masking, and no bus protocol errors.
- timer_watchdog_constrained_random: Randomize prescaler, comparator thresholds, watchdog thresholds, enable/mask/lock sequences, and periodic pet timing to explore mixed timer/watchdog interactions within a short run.
- interrupt_state_random_sequence: Randomly exercise INTR_TEST, INTR_ENABLE, and W1C clearing sequences while checking that output pins reflect masked raw state correctly.

## Risk Areas
- Watchdog lock semantics (high): Lock is sticky until reset and can easily be implemented incorrectly, especially around write restrictions and pet accessibility.
- 64-bit timer comparator partial writes (high): Non-atomic LOW/HIGH programming can create transient compare conditions and is a common source of off-by-one or glitch bugs.
- Prescaler update timing (high): Specification requires new prescaler value to take effect on the next boundary without resetting the internal prescale counter.
- Interrupt masking and W1C behavior (medium): INTR_STATE, INTR_ENABLE, and INTR_TEST interaction is a frequent integration bug and directly affects software-visible behavior.
- Watchdog bark/bite threshold ordering (medium): Bark should raise an interrupt before bite asserts alert_o; threshold equality and escalation ordering need explicit checking.
- Reserved-bit handling and CSR decode (medium): Upper bits must read as zero and writes must not perturb state; decode mistakes can corrupt adjacent registers.
- Reset and post-reset recovery (medium): Reset must clear counters, interrupts, alert state, and lock state; recovery after fatal watchdog conditions is essential.
- TL-UL protocol compliance under simple traffic (low): Even with limited budget, basic read/write handshakes, back-to-back accesses, and address alignment should be validated.
