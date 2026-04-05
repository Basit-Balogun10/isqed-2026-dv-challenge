# bastion_gpio Coverage Gaps

## Coverage Snapshot

- Line coverage: 73.21%
- Branch coverage: 13.77%

## Uncovered Code Regions

| Gap ID | File | Line Range | Reason Uncovered |
|--------|------|------------|------------------|
| GAP-005 | duts/bastion_gpio/bastion_gpio.sv | 42-48 | Reference traffic only validates basic data/dir behavior and does not iterate through all interrupt mode control CSRs. |
| GAP-006 | duts/bastion_gpio/bastion_gpio.sv | 217-220 | Masked output lower-half writes are not explicitly used, so per-bit write-enable loops are largely untouched. |
| GAP-007 | duts/bastion_gpio/bastion_gpio.sv | 224-227 | Upper-half masked writes are missing from baseline tests, leaving the mirrored write loop under-covered. |
| GAP-008 | duts/bastion_gpio/bastion_gpio.sv | 50-52 | Input toggles are not timed to stress synchronizer pipeline latency and previous-sample edge comparisons. |

## Unhit Functional Coverage Bins (Estimated From VPlan)

| Gap ID | Coverpoint | Bin Name | Required Stimulus |
|--------|------------|----------|-------------------|
| GAP-005 | vp_scenario_id | VP-GPIO-004, VP-GPIO-005, VP-GPIO-006 | Program all edge/level interrupt control banks and confirm each mode can independently assert per-pin interrupts. |
| GAP-006 | vp_scenario_id | VP-GPIO-011, VP-GPIO-012 | Validate masked lower-half writes with sparse and dense mask patterns while preserving untouched bits. |
| GAP-007 | vp_scenario_id | VP-GPIO-013, VP-GPIO-014 | Exercise MASKED_OUT_UPPER with mixed masks and verify independent control of upper 16 output bits. |
| GAP-008 | vp_scenario_id | VP-GPIO-002, VP-GPIO-003 | Create back-to-back asynchronous GPIO transitions to validate q1/q2/prev synchronization and edge detection latency. |

## Root Cause And Intent

### GAP-005 - interrupt_mode_register_bank
- Root cause: Reference traffic only validates basic data/dir behavior and does not iterate through all interrupt mode control CSRs.
- Test intent: Program all edge/level interrupt control banks and confirm each mode can independently assert per-pin interrupts.

### GAP-006 - masked_out_lower_update
- Root cause: Masked output lower-half writes are not explicitly used, so per-bit write-enable loops are largely untouched.
- Test intent: Validate masked lower-half writes with sparse and dense mask patterns while preserving untouched bits.

### GAP-007 - masked_out_upper_update
- Root cause: Upper-half masked writes are missing from baseline tests, leaving the mirrored write loop under-covered.
- Test intent: Exercise MASKED_OUT_UPPER with mixed masks and verify independent control of upper 16 output bits.

### GAP-008 - input_synchronizer_pipeline
- Root cause: Input toggles are not timed to stress synchronizer pipeline latency and previous-sample edge comparisons.
- Test intent: Create back-to-back asynchronous GPIO transitions to validate q1/q2/prev synchronization and edge detection latency.
