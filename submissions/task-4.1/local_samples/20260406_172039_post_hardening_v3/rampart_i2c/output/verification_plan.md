# Verification Plan

## Features
- TL-UL CSR read/write access
- Reset behavior and CSR reset values
- Open-drain SCL/SDA drive and loopback behavior
- Host mode enable/disable and basic command sequencing
- Target mode enable/disable and TX/RX data path
- Format FIFO push/pop and status flags
- RX FIFO and ACQ FIFO readout
- FIFO reset controls
- Timing CSR programming and retention
- Target ID/address mask programming
- Interrupt state/enable/test behavior
- Host timeout configuration and timeout indication
- Arbitration loss and bus contention response
- Multi-role simultaneous enable behavior
- Bus override/debug control
- Basic I2C start/stop/address/data transaction flow

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_csr_map: Apply reset, verify all documented CSRs reset to expected values, confirm RO/WO/RW/W1C access behavior, and sanity-check TL-UL read/write responses across the full register map.
- open_drain_idle_and_loopback: Verify SCL/SDA are never driven high, output enables control pull-low behavior, and CTRL.line_loopback correctly routes outputs back to inputs for internal self-observation.
- host_basic_write_sequence: Enable host mode, program timing CSRs with safe values, push a minimal format FIFO command sequence, and confirm start/address/data/stop activity on the I2C pins.
- host_basic_read_sequence: Exercise a host read transaction, confirm RX FIFO captures returned data, and validate RDATA readout and empty/full status transitions.
- target_basic_transmit_receive: Enable target mode, program TARGET_ID, preload TX FIFO, emulate an external host transaction, and verify target transmit/receive paths plus ACQDATA readout.
- fifo_status_and_reset_controls: Fill and drain format, TX, RX, and ACQ FIFOs to observe status flags, then apply FIFO_CTRL resets and confirm levels and empty/full indicators clear correctly.
- interrupt_state_enable_test: Program INTR_ENABLE, inject interrupts via INTR_TEST, observe INTR_STATE set behavior, and clear selected bits using W1C writes.
- timeout_and_arbitration_loss: Configure a short host timeout and a forced arbitration-loss scenario to verify timeout/arb-loss status, interrupt generation, and safe bus release.
- simultaneous_host_target_enable: Enable both host and target modes together, drive bus activity from an external agent, and confirm internal arbitration and role selection do not deadlock.

## Random Tests
- tlul_csr_fuzz_sanitized: Run constrained-random TL-UL reads/writes over the 19-register map with legal opcodes and byte enables, checking for protocol stability, no X-propagation, and correct RO/WO protection.
- i2c_host_sequence_randomized: Generate randomized but legal host command streams through FDATA with varying timing CSR settings, data lengths, repeated starts, and stop conditions to stress host FSM transitions.
- i2c_target_traffic_randomized: Randomize target-mode transactions, target address matches/mismatches, TX FIFO payloads, and external master read/write patterns to stress target FSM and ACQ/RX behavior.
- contention_and_bus_noise_randomized: Inject randomized external SCL/SDA behavior, including contention, delayed pull-ups, and arbitration edge cases, to validate open-drain robustness and error recovery.

## Risk Areas
- Host FSM transaction sequencing (high): Most likely source of functional bugs due to multiple timing CSRs, format FIFO decoding, and start/stop/address/data sequencing complexity.
- Target FSM and dual-role arbitration (high): Two independent FSMs share the same physical bus, creating high risk of deadlock, incorrect role handoff, or missed bus events.
- FIFO boundary conditions (high): Four 64-entry FIFOs plus status flags and reset controls create overflow/underflow and off-by-one risks.
- Interrupt and timeout behavior (medium): W1C semantics, enable masking, test injection, and timeout generation are common integration failure points and easy to regress quickly.
- Open-drain pin behavior and loopback (medium): Incorrect drive-high behavior or loopback wiring can break bus interoperability while still passing simple CSR tests.
- TL-UL access protection and register semantics (medium): RO/WO/W1C behavior, reserved-bit handling, and response correctness must be validated but are lower risk than bus-state logic.
- Timing CSR programming across speed modes (low): Programmable timing parameters can expose corner cases, but exhaustive speed characterization is not feasible within the 60-minute budget.
