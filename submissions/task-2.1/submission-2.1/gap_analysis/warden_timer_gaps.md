# warden_timer Coverage Gaps

## Coverage Snapshot

- Line coverage: 71.28%
- Branch coverage: 20.66%

## Uncovered Code Regions

| Gap ID | File | Line Range | Reason Uncovered |
|--------|------|------------|------------------|
| GAP-009 | duts/warden_timer/warden_timer.sv | 293-297 | Watchdog lock escalation and post-lock write attempts are not attempted in baseline flows. |
| GAP-010 | duts/warden_timer/warden_timer.sv | 316-319 | Partial-byte writes to bark threshold are not covered, missing byte-mask corner cases on threshold programming. |
| GAP-011 | duts/warden_timer/warden_timer.sv | 250-253 | Comparator-1 tests are sparse and do not apply partial low-word writes with byte masks. |
| GAP-012 | duts/warden_timer/warden_timer.sv | 257-260 | Upper-word programming of MTIMECMP1 is not deeply exercised, leaving masked high-byte paths uncovered. |

## Unhit Functional Coverage Bins (Estimated From VPlan)

| Gap ID | Coverpoint | Bin Name | Required Stimulus |
|--------|------------|----------|-------------------|
| GAP-009 | vp_scenario_id | VP-TIMER-009, VP-TIMER-010 | Lock watchdog control and verify subsequent writes cannot disable lock or mutate protected control fields. |
| GAP-010 | vp_scenario_id | VP-TIMER-012, VP-TIMER-013 | Use partial TL-UL masks to program bark threshold bytes and check bark interrupt timing consistency. |
| GAP-011 | vp_scenario_id | VP-TIMER-004, VP-TIMER-005 | Program MTIMECMP1 low word via masked writes and verify timer1 expiry behavior follows merged value. |
| GAP-012 | vp_scenario_id | VP-TIMER-006, VP-TIMER-014 | Apply partial high-word writes and validate 64-bit compare behavior around rollover boundaries. |

## Root Cause And Intent

### GAP-009 - watchdog_lock_gating
- Root cause: Watchdog lock escalation and post-lock write attempts are not attempted in baseline flows.
- Test intent: Lock watchdog control and verify subsequent writes cannot disable lock or mutate protected control fields.

### GAP-010 - watchdog_bark_threshold_bytes
- Root cause: Partial-byte writes to bark threshold are not covered, missing byte-mask corner cases on threshold programming.
- Test intent: Use partial TL-UL masks to program bark threshold bytes and check bark interrupt timing consistency.

### GAP-011 - mtimecmp1_low_partial_write
- Root cause: Comparator-1 tests are sparse and do not apply partial low-word writes with byte masks.
- Test intent: Program MTIMECMP1 low word via masked writes and verify timer1 expiry behavior follows merged value.

### GAP-012 - mtimecmp1_high_partial_write
- Root cause: Upper-word programming of MTIMECMP1 is not deeply exercised, leaving masked high-byte paths uncovered.
- Test intent: Apply partial high-word writes and validate 64-bit compare behavior around rollover boundaries.
