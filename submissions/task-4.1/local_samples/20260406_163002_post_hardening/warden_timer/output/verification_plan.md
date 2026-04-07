# Verification Plan

## Features
- TL-UL CSR read/write access for 15-register map
- Reset behavior for all CSRs, counters, interrupts, and alert
- 64-bit mtime free-running counter with 12-bit prescaler
- Prescaler programming and boundary behavior
- 64-bit timer comparator 0 interrupt generation
- 64-bit timer comparator 1 interrupt generation
- Comparator partial-write behavior across LOW/HIGH halves
- INTR_STATE W1C behavior
- INTR_ENABLE masking behavior
- INTR_TEST software-forced interrupt behavior
- Watchdog enable/disable operation
- Watchdog bark threshold interrupt generation
- Watchdog bite threshold alert generation
- Watchdog pet write side effect
- Watchdog lock behavior and write restrictions
- Read-only and write-only register access enforcement
- Reserved-bit read-as-zero / write-ignore behavior
- Concurrent timer and watchdog activity under bus traffic

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_and_csr_map: Verify reset values for all visible CSRs, confirm TL-UL reads/writes to each implemented register, and check that mtime and watchdog count start at zero with interrupts and alert deasserted.
- mtime_prescaler_basic: Program prescaler values 0, 1, and a mid-range value to confirm mtime increments at the expected rate and remains monotonic across prescaler changes.
- timer0_compare_interrupt: Program MTIMECMP0 below and above current mtime, enable intr_o[0], and verify raw interrupt, masked output, and W1C clear behavior.
- timer1_compare_interrupt: Repeat comparator validation for MTIMECMP1, including independent operation from timer0 and correct interrupt enable masking.
- comparator_partial_write_ordering: Write LOW then HIGH and HIGH then LOW for 64-bit comparator programming while mtime is active, checking intermediate compare behavior and final threshold correctness.
- intr_test_and_w1c: Use INTR_TEST to force each interrupt bit, confirm INTR_STATE sets, verify output gating through INTR_ENABLE, and clear each bit with W1C writes.
- watchdog_enable_bark_bite: Enable watchdog, program bark and bite thresholds, observe bark interrupt before bite alert, and confirm alert_o asserts at bite threshold.
- watchdog_pet_resets_counter: Pet the watchdog before bark threshold and verify the counter returns to zero and no bark or bite occurs.
- watchdog_lock_behavior: Set wd_lock, attempt to clear lock and modify watchdog control fields, verify lock is sticky until reset, and confirm WATCHDOG_PET remains writable.
- reserved_bits_and_access_policy: Write non-zero values to reserved bits and read back to confirm RAZ/WI behavior; also attempt reads from WO register and writes to RO register to ensure no unintended side effects.

## Random Tests
- tlul_csr_fuzz_with_scoreboard: Run constrained-random TL-UL reads/writes across the 64-byte window with a mirrored CSR model, checking access permissions, reset defaults, and reserved-bit behavior.
- timer_watchdog_concurrent_stress: Randomize prescaler, comparator thresholds, watchdog thresholds, enable masks, and pet timing while continuously checking mtime monotonicity, interrupt correctness, and alert generation.
- partial_64bit_programming_fuzz: Randomize the order and spacing of LOW/HIGH writes for both comparators to expose transient compare hazards and ensure final programmed values are honored.
- interrupt_masking_and_clear_stress: Randomly toggle INTR_ENABLE and issue W1C clears while interrupts are pending to validate output gating and state retention semantics.

## Risk Areas
- Watchdog bark/bite sequencing (high): Highest functional risk because two escalation thresholds and a fatal alert must occur in the correct order under continuous counting and bus activity.
- Watchdog lock stickiness (high): Lock behavior is security-sensitive and easy to implement incorrectly; it must survive writes and only clear on reset.
- 64-bit comparator partial-write behavior (high): Split LOW/HIGH programming can create transient compare conditions and is a common source of off-by-one or glitch bugs.
- Prescaler boundary and update timing (medium): Changing prescaler while active can introduce subtle timing errors if the new value is applied too early or too late.
- Interrupt state/mask/test semantics (medium): INTR_STATE W1C, INTR_ENABLE masking, and INTR_TEST forcing must interact correctly to avoid false or stuck interrupts.
- Reset and access policy compliance (medium): RO/WO/RW behavior, reserved bits, and reset defaults are straightforward but essential for CSR correctness.
- Concurrent timer and watchdog operation (low): Simultaneous activity can expose shared-clock or arbitration issues, but is lower risk than core functional correctness.
