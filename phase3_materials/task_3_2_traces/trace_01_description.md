# Trace 01: Warden Timer — TOCTOU Split Write Spurious Interrupt

## Failing Assertion

```
ASSERTION FAILED: assert_no_spurious_timer0
  Location: warden_timer_sva.sv:42
  Message: "timer0 interrupt shall not assert before mtime reaches mtimecmp0 target value"
  Failure time: cycle 150
```

## Spec Requirement

From the Warden Timer Specification, Section 3.2.1:

> **Timer Compare Registers (mtimecmp0, mtimecmp1):** These 64-bit registers define the
> timer expiration threshold. The timer interrupt (intr_state[0] or intr_state[1]) asserts
> when mtime >= mtimecmpN. Writing to mtimecmp SHALL NOT generate spurious interrupts.
> Software may write the 64-bit value using two 32-bit bus transactions; the hardware must
> ensure atomicity of the comparison.

## Test Scenario

The test performs the following sequence:

1. Reset the timer (mtime starts at 0, mtimecmp0 = 0)
2. Set prescaler to 0 (mtime increments every cycle)
3. Enable timer0 interrupt (intr_enable[0] = 1)
4. Write mtimecmp0 to 0x0000_0001_0000_0050 using two 32-bit writes:
   - First: Write MTIMECMP0_LOW (address 0x08) = 0x0000_0050
   - Second: Write MTIMECMP0_HIGH (address 0x0C) = 0x0000_0001
5. Expected: No interrupt until mtime reaches 0x0000_0001_0000_0050

## Observed Behavior

The timer0 interrupt fires at cycle 150, when mtime is approximately 0x96 (150 decimal).
This is far before the intended target of 0x0000_0001_0000_0050. The interrupt should not
have fired until mtime reached the full 64-bit target value.

## Signal Trace File

See `trace_01_signals.csv` for cycle-by-cycle signal values around the failure point.
Key signals to examine:
- `mtime_q[63:0]` — the free-running timer counter
- `mtimecmp0_q[63:0]` — the comparison target (watch for intermediate values)
- `timer0_expired` — the comparison result
- `intr_state_q[0]` — the interrupt state bit
- `tl_is_write` and `tl_addr` — bus write transactions
