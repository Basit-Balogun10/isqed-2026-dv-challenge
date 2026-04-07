# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_smoke: Apply reset, verify all 19 CSRs are reachable over TL-UL, confirm reset values for CTRL/interrupt-related registers, and validate RO/WO/RW access behavior including reserved-bit masking.
# - open_drain_loopback_basic: Enable line loopback and verify SCL/SDA open-drain behavior: outputs only drive low, released lines read high via pull-up, and loopback reflects internal drive decisions.
# - host_mode_basic_transaction: Enable host mode, program timing registers with safe values, push a minimal format FIFO command sequence, and check expected bus activity plus RX FIFO/status updates.
# - target_mode_tx_acq_smoke: Enable target mode, preload TX data, stimulate an external host transaction, and verify TX data consumption and ACQDATA capture behavior.
# - interrupt_register_semantics: Exercise INTR_ENABLE, INTR_TEST, and INTR_STATE W1C behavior by injecting a subset of interrupts, observing status set/clear behavior, and confirming masked interrupts do not propagate.
# - fifo_reset_and_status: Write FIFO_CTRL reset controls, confirm FIFO_STATUS and STATUS reflect empty/full transitions, and verify read/write ports behave correctly after reset.
# - timeout_and_arbitration_smoke: Use constrained bus stimuli to provoke timeout or arbitration-loss indications at least once, then confirm the DUT reports the condition without deadlocking TL-UL access.
#
# Random tests:
# - csr_fuzz_with_protocol_sanity: Randomize TL-UL reads/writes across the CSR map with legal opcodes and byte enables, checking mirrored readback, access permissions, and reserved-bit stability.
# - host_command_stream_random: Generate randomized but legal host format FIFO command streams with varying timing CSR settings, while monitoring for forward progress, FIFO boundary behavior, and no protocol violations.
# - target_host_interaction_random: Randomize target-mode TX preload, external I2C master transactions, and enable combinations to stress concurrent host/target FSM interaction and acquire path capture.
# - interrupt_and_status_random: Randomly toggle interrupt enables, inject interrupt tests, and sample STATUS/FIFO_STATUS under mixed activity to validate sticky, masked, and W1C behavior.
