# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_smoke: Apply reset, verify all readable CSRs return documented defaults, confirm write-only registers ignore reads, and exercise basic TL-UL read/write handshakes on CTRL, TIMING, TARGET_ID, INTR_ENABLE, and INTR_TEST.
# - open_drain_and_loopback_sanity: Program CTRL.line_loopback and verify SCL/SDA output enables only ever drive low or release, then confirm internal loopback reflects driven bus state back into inputs.
# - host_basic_start_stop: Enable host mode, push a minimal format FIFO command sequence, and verify START/STOP generation, bus busy/idle status transitions, and no unexpected alert.
# - host_fifo_status_and_readback: Fill and drain the format FIFO to hit empty/full boundaries, check STATUS and FIFO_STATUS flags, and verify RDATA returns host RX data when loopback or stimulus provides incoming bytes.
# - target_tx_acq_paths: Enable target mode, write TXDATA entries, stimulate target receive activity, and verify ACQDATA reads back captured bytes while TX FIFO status reflects occupancy.
# - interrupt_w1c_and_test_injection: Enable selected interrupts, inject them through INTR_TEST, confirm INTR_STATE sets, then clear via W1C writes and verify masking behavior with INTR_ENABLE.
# - timeout_and_arbitration_loss: Program a short HOST_TIMEOUT_CTRL, hold the bus in a non-progressing state to trigger timeout indication, and create a multi-master conflict to observe arbitration loss handling and recovery.
# - simultaneous_host_target_enable: Enable both host and target modes together, drive representative bus activity, and verify the DUT resolves role ownership without illegal simultaneous drive on SCL/SDA.
#
# Random tests:
# - csr_fuzz_smoke: Randomize legal TL-UL reads and writes across all 19 CSRs with constrained field masks, checking for stable readback, no protocol errors, and correct handling of reserved bits.
# - fifo_pressure_random: Randomly push host format commands, target TX data, and read RX/ACQ paths under backpressure to stress FIFO boundary conditions, empty/full transitions, and data ordering.
# - i2c_role_mix_random: Randomly toggle host_enable, target_enable, and line_loopback while generating I2C bus activity to explore FSM interactions, arbitration edges, and unexpected state combinations.
# - timing_register_randomization: Sweep timing CSRs across representative legal values to ensure programming does not corrupt operation and that bus activity remains coherent across timing configurations.
