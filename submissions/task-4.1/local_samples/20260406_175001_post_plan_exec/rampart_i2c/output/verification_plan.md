# Verification Plan

## Features
- TL-UL CSR read/write access with byte/word integrity checks
- Reset behavior and CSR default value validation
- Host mode enable/disable sequencing
- Target mode enable/disable sequencing
- Open-drain SCL/SDA output-enable behavior
- CTRL line_loopback functional path
- Timing CSR programming and readback
- Format FIFO write path and status flags
- Host RX FIFO read path and status flags
- Target TX FIFO write path and status flags
- Target ACQ FIFO read path and status flags
- Interrupt state/enable/test behavior
- W1C interrupt clearing
- Bus override register behavior
- Host timeout configuration and timeout indication
- Arbitration loss and bus conflict handling
- I2C START/STOP and basic byte transfer sequencing
- Multi-role coexistence and role arbitration
- TL-UL backpressure and response integrity
- Alert pin sanity on fatal/illegal conditions

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_smoke: Apply reset, verify all readable CSRs return documented defaults, confirm write-only registers ignore reads, and exercise basic TL-UL read/write handshakes on CTRL, TIMING, TARGET_ID, INTR_ENABLE, and INTR_TEST.
- open_drain_and_loopback_sanity: Program CTRL.line_loopback and verify SCL/SDA output enables only ever drive low or release, then confirm internal loopback reflects driven bus state back into inputs.
- host_basic_start_stop: Enable host mode, push a minimal format FIFO command sequence, and verify START/STOP generation, bus busy/idle status transitions, and no unexpected alert.
- host_fifo_status_and_readback: Fill and drain the format FIFO to hit empty/full boundaries, check STATUS and FIFO_STATUS flags, and verify RDATA returns host RX data when loopback or stimulus provides incoming bytes.
- target_tx_acq_paths: Enable target mode, write TXDATA entries, stimulate target receive activity, and verify ACQDATA reads back captured bytes while TX FIFO status reflects occupancy.
- interrupt_w1c_and_test_injection: Enable selected interrupts, inject them through INTR_TEST, confirm INTR_STATE sets, then clear via W1C writes and verify masking behavior with INTR_ENABLE.
- timeout_and_arbitration_loss: Program a short HOST_TIMEOUT_CTRL, hold the bus in a non-progressing state to trigger timeout indication, and create a multi-master conflict to observe arbitration loss handling and recovery.
- simultaneous_host_target_enable: Enable both host and target modes together, drive representative bus activity, and verify the DUT resolves role ownership without illegal simultaneous drive on SCL/SDA.

## Random Tests
- csr_fuzz_smoke: Randomize legal TL-UL reads and writes across all 19 CSRs with constrained field masks, checking for stable readback, no protocol errors, and correct handling of reserved bits.
- fifo_pressure_random: Randomly push host format commands, target TX data, and read RX/ACQ paths under backpressure to stress FIFO boundary conditions, empty/full transitions, and data ordering.
- i2c_role_mix_random: Randomly toggle host_enable, target_enable, and line_loopback while generating I2C bus activity to explore FSM interactions, arbitration edges, and unexpected state combinations.
- timing_register_randomization: Sweep timing CSRs across representative legal values to ensure programming does not corrupt operation and that bus activity remains coherent across timing configurations.

## Risk Areas
- Host/target FSM interaction (high): Two independent FSMs share SCL/SDA and can be enabled simultaneously; this is the highest functional risk for deadlock, illegal drive, or missed arbitration.
- FIFO boundary behavior (high): Four 64-entry FIFOs plus status flags create common off-by-one and underflow/overflow risks, especially around empty/full transitions and read/write ordering.
- Open-drain bus control (high): SCL/SDA must never be actively driven high; incorrect output-enable behavior can break bus correctness and is easy to miss without explicit checks.
- Interrupt and alert signaling (medium): INTR_STATE, INTR_ENABLE, INTR_TEST, and alert_o are often partially implemented or miswired; these are high-value checks with low test cost.
- Timeout and arbitration loss (medium): These are protocol corner cases that depend on bus timing and external stimulus; they are important but may require careful stimulus to observe reliably within the time budget.
- Timing CSR programming (medium): Multiple programmable timing registers increase configuration space, but most bugs will be caught by a small representative sweep rather than exhaustive exploration.
- Reserved field and write-only register handling (low): Lower functional risk, but useful for confirming CSR robustness and TL-UL compliance.
