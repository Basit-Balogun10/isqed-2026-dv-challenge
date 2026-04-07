# Verification Plan

## Features
- TL-UL CSR read/write access with same-cycle response checking
- Reset behavior and CSR reset-value validation
- Open-drain SCL/SDA modeling with pull-up and contention-aware sampling
- Host mode enable/disable and basic command sequencing
- Target mode enable/disable and transmit/acquire data path checks
- FIFO control and status behavior for format, RX, TX, and acquire paths
- Interrupt state/enable/test CSR behavior including W1C semantics
- Timing CSR programming smoke checks across all timing registers
- Bus override and line loopback functional checks
- Arbitration-loss and timeout/error-path observation at a smoke-test level
- Concurrent host/target enable interaction under simple bus conditions

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_smoke: Apply reset, verify all 19 CSRs are reachable over TL-UL, confirm reset values for CTRL/interrupt-related registers, and validate RO/WO/RW access behavior including reserved-bit masking.
- open_drain_loopback_basic: Enable line loopback and verify SCL/SDA open-drain behavior: outputs only drive low, released lines read high via pull-up, and loopback reflects internal drive decisions.
- host_mode_basic_transaction: Enable host mode, program timing registers with safe values, push a minimal format FIFO command sequence, and check expected bus activity plus RX FIFO/status updates.
- target_mode_tx_acq_smoke: Enable target mode, preload TX data, stimulate an external host transaction, and verify TX data consumption and ACQDATA capture behavior.
- interrupt_register_semantics: Exercise INTR_ENABLE, INTR_TEST, and INTR_STATE W1C behavior by injecting a subset of interrupts, observing status set/clear behavior, and confirming masked interrupts do not propagate.
- fifo_reset_and_status: Write FIFO_CTRL reset controls, confirm FIFO_STATUS and STATUS reflect empty/full transitions, and verify read/write ports behave correctly after reset.
- timeout_and_arbitration_smoke: Use constrained bus stimuli to provoke timeout or arbitration-loss indications at least once, then confirm the DUT reports the condition without deadlocking TL-UL access.

## Random Tests
- csr_fuzz_with_protocol_sanity: Randomize TL-UL reads/writes across the CSR map with legal opcodes and byte enables, checking mirrored readback, access permissions, and reserved-bit stability.
- host_command_stream_random: Generate randomized but legal host format FIFO command streams with varying timing CSR settings, while monitoring for forward progress, FIFO boundary behavior, and no protocol violations.
- target_host_interaction_random: Randomize target-mode TX preload, external I2C master transactions, and enable combinations to stress concurrent host/target FSM interaction and acquire path capture.
- interrupt_and_status_random: Randomly toggle interrupt enables, inject interrupt tests, and sample STATUS/FIFO_STATUS under mixed activity to validate sticky, masked, and W1C behavior.

## Risk Areas
- Host/target FSM interaction and arbitration (high): Two independent FSMs share SCL/SDA and the spec explicitly allows simultaneous enable with bus-condition-dependent behavior; this is the highest functional ambiguity and likely bug source.
- FIFO boundary and reset behavior (high): Four 64-entry FIFOs plus reset controls create high risk for off-by-one, stale-status, and underflow/overflow issues that are practical to expose within a short run.
- Open-drain line handling and loopback (high): Incorrect drive/release behavior can break all bus transactions and is easy to miss without explicit contention-aware checks.
- Interrupt state/enable/test semantics (medium): W1C and test-injection logic are common integration failure points and can be validated quickly with directed CSR tests.
- Timing CSR programming (medium): Multiple programmable timing registers increase configuration space; basic smoke coverage is needed, but exhaustive timing validation is out of scope for a 60-minute budget.
- Timeout and arbitration-loss reporting (medium): Error-path observability is important, but full protocol corner-case exploration is expensive; a smoke-level check is sufficient for this budget.
- Reserved-bit and access-type enforcement (low): Lower functional risk, but easy to cover through CSR smoke and random access tests.
