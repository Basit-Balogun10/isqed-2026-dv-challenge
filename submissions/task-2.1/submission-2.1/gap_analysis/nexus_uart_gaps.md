# nexus_uart Coverage Gaps

## Coverage Snapshot

- Line coverage: 60.08%
- Branch coverage: 14.49%

## Uncovered Code Regions

| Gap ID | File | Line Range | Reason Uncovered |
|--------|------|------------|------------------|
| GAP-001 | duts/nexus_uart/nexus_uart.sv | 523-533 | Reference smoke runs do not vary baud divisors and sample-phase stress, so the RX start-bit qualification and oversampling transitions remain mostly untouched. |
| GAP-002 | duts/nexus_uart/nexus_uart.sv | 587-595 | Current tests avoid malformed stop sequences and FIFO pressure, so STOP2 frame-error and overflow interactions are rarely exercised. |
| GAP-003 | duts/nexus_uart/nexus_uart.sv | 401-406 | TX tests stay on one parity setting, leaving parity/no-parity branch selection under-covered. |
| GAP-004 | duts/nexus_uart/nexus_uart.sv | 422-426 | One-stop-bit default stimulus bypasses stop-bit mode muxing and TX_STOP2 entry conditions. |

## Unhit Functional Coverage Bins (Estimated From VPlan)

| Gap ID | Coverpoint | Bin Name | Required Stimulus |
|--------|------------|----------|-------------------|
| GAP-001 | vp_scenario_id | VP-UART-001, VP-UART-003, VP-UART-011 | Drive randomized baud divisors with phase-offset start bits and verify RX state transitions and sampled data alignment. |
| GAP-002 | vp_scenario_id | VP-UART-007, VP-UART-010, VP-UART-014 | Exercise 2-stop-bit mode with bad stop levels and near-full RX FIFO to validate frame-error and overflow behavior. |
| GAP-003 | vp_scenario_id | VP-UART-004, VP-UART-005 | Run directed TX bursts in parity disabled/even/odd modes and verify transmitted parity bit policy. |
| GAP-004 | vp_scenario_id | VP-UART-006, VP-UART-012 | Toggle stop-bit configuration and confirm stop-bit count on the serial line for consecutive frames. |

## Root Cause And Intent

### GAP-001 - rx_oversample_start_path
- Root cause: Reference smoke runs do not vary baud divisors and sample-phase stress, so the RX start-bit qualification and oversampling transitions remain mostly untouched.
- Test intent: Drive randomized baud divisors with phase-offset start bits and verify RX state transitions and sampled data alignment.

### GAP-002 - rx_stop2_and_error_latch
- Root cause: Current tests avoid malformed stop sequences and FIFO pressure, so STOP2 frame-error and overflow interactions are rarely exercised.
- Test intent: Exercise 2-stop-bit mode with bad stop levels and near-full RX FIFO to validate frame-error and overflow behavior.

### GAP-003 - tx_parity_branch_select
- Root cause: TX tests stay on one parity setting, leaving parity/no-parity branch selection under-covered.
- Test intent: Run directed TX bursts in parity disabled/even/odd modes and verify transmitted parity bit policy.

### GAP-004 - tx_stop_bit_mode_select
- Root cause: One-stop-bit default stimulus bypasses stop-bit mode muxing and TX_STOP2 entry conditions.
- Test intent: Toggle stop-bit configuration and confirm stop-bit count on the serial line for consecutive frames.
