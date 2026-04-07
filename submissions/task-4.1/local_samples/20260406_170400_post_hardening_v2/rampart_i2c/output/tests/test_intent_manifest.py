# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_csr_defaults: Apply reset, verify all readable CSRs return documented reset/default values, writable CSRs accept writes, reserved bits read as zero, and TL-UL read/write handshakes complete cleanly.
# - csr_rw_ro_wo_w1c_sanity: Exercise each CSR access type: RW readback, RO immutability, WO write acceptance with no meaningful readback, and W1C clearing of INTR_STATE bits.
# - fifo_reset_and_status_flags: Write FIFO_CTRL reset controls, confirm FIFO_STATUS and STATUS reflect empty/full transitions, and verify no stale data remains after reset.
# - host_mode_single_byte_write: Enable host mode, program timing CSRs, enqueue a simple format command, and verify SCL/SDA open-drain activity and completion status for a minimal write transaction.
# - host_mode_readback_path: Perform a host read transaction and confirm received data appears in RDATA/RX FIFO path with expected status and interrupt behavior.
# - target_mode_receive_and_acquire: Enable target mode, match TARGET_ID, drive an external host transaction, and verify received bytes are captured in ACQDATA with correct status updates.
# - target_mode_transmit_path: Preload TXDATA, trigger a target read response, and verify the controller sources data correctly on SDA while maintaining open-drain semantics.
# - interrupt_state_enable_test: Induce representative events, verify INTR_STATE bits set, mask/unmask with INTR_ENABLE, inject via INTR_TEST, and clear with W1C writes.
# - line_loopback_functional: Enable CTRL.line_loopback and confirm internal routing of SCL/SDA allows self-contained transaction progress without external bus drivers.
# - arbitration_loss_scenario: Create a multi-master contention case on SDA, verify arbitration loss detection, bus release behavior, and recovery to idle.
# - timeout_configuration_and_expiry: Program HOST_TIMEOUT_CTRL to a short threshold, stall bus progress, and verify timeout status/interrupt behavior and safe recovery.
# - ovrd_debug_override: Exercise OVRD to force bus line states, confirm override precedence over normal FSM drive, and ensure outputs remain open-drain compliant.
#
# Random tests:
# - tlul_csr_fuzz_smoke: Randomized TL-UL read/write sequences over all implemented CSRs with scoreboarding for access policy, reset persistence, and reserved-bit masking.
# - host_fsm_random_transactions: Constrained-random host-mode command generation covering start/stop/read/write/restart patterns, varying timing CSRs and FIFO depths to hit host FSM branches.
# - target_fsm_random_transactions: Constrained-random target-mode stimulus with randomized address matches, read/write directions, and TX/ACQ FIFO interactions to exercise target FSM branches.
# - mixed_role_contention_random: Randomly enable host and target together, vary external bus activity, and check arbitration, bus ownership, and no illegal simultaneous drive on SCL/SDA.
# - interrupt_and_timeout_random: Randomly toggle interrupt enables, inject test interrupts, and vary timeout settings while transactions are in flight to validate event reporting robustness.
