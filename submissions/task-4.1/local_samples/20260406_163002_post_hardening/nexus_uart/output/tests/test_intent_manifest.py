# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_csr_map: Verify reset defaults for all 8 CSRs, TL-UL read/write access, reserved-bit behavior, and unmapped address error response.
# - ctrl_programming_sanity: Program CTRL with representative combinations of tx_enable, rx_enable, parity_mode, stop_bits, and baud_divisor; confirm readback and no protocol errors.
# - tx_fifo_basic_push_pop: Write a small sequence to TXDATA, observe STATUS level/empty/full transitions, and confirm TX FIFO accepts data when enabled.
# - rx_loopback_basic: Enable loopback, transmit a few bytes, and verify they are received in order through RXDATA with matching STATUS updates.
# - fifo_watermark_interrupts: Program TX/RX watermarks, drive FIFO levels across thresholds, and verify INTR_STATE assertion and W1C clearing behavior.
# - fifo_reset_and_sticky_error_clear: Force RX overrun or parity/frame error conditions if achievable, then verify FIFO_CTRL reset clears sticky STATUS bits and flushes FIFOs.
# - parity_stopbit_matrix_smoke: Exercise even/odd/no parity and 1/2 stop-bit settings with a minimal set of loopback frames to confirm no obvious framing failures.
# - baud_divisor_sweep_small: Run a short sweep of representative baud_divisor values, including a mid-range value and a corner value near minimum legal operation, to validate timing robustness.
#
# Random tests:
# - tlul_csr_fuzz: Randomize legal CSR reads/writes, reserved-bit writes, and occasional unmapped accesses while checking TL-UL response integrity and register invariants.
# - uart_loopback_fifo_stress: Randomly generate TX bursts, RX consumption delays, and loopback enable patterns to stress FIFO occupancy, watermark interrupts, and data ordering.
# - config_mixed_stress: Randomly vary CTRL and FIFO_CTRL settings between short traffic bursts to expose state-machine corner cases across TX, RX, and interrupt logic.
