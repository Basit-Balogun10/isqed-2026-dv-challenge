# Auto-generated test intent summary
#
# Directed tests:
# - reset_and_csr_smoke: Verify reset defaults for all 8 CSRs, reserved bits read as zero, write-ignore behavior on reserved fields, and basic TL-UL read/write access to CTRL, STATUS, TXDATA, RXDATA, FIFO_CTRL, and interrupt registers.
# - tlul_unmapped_address_error: Issue reads and writes to unmapped addresses and confirm error responses while preserving DUT stability and subsequent legal access functionality.
# - ctrl_programming_sweep: Program representative CTRL combinations for tx_enable/rx_enable, baud_divisor, parity_mode, stop_bits, and loopback_en; confirm register readback and no protocol or CSR decode issues.
# - tx_fifo_fill_and_full_status: Write TXDATA until TX FIFO reaches full, verify tx_fifo_level and tx_fifo_full transitions, and confirm additional writes are handled according to peripheral behavior without corrupting status.
# - rx_fifo_read_and_empty_status: Inject receive bytes through uart_rx_i or loopback, read RXDATA until empty, and verify rx_fifo_level, rx_fifo_empty, and data ordering.
# - loopback_basic_data_path: Enable loopback and transmit a small set of bytes through TXDATA, then verify the same bytes are observed on RXDATA with correct ordering and status updates.
# - fifo_flush_clears_levels: Populate TX and RX FIFOs, assert tx_fifo_rst and rx_fifo_rst independently via FIFO_CTRL, and verify FIFO levels return to empty and sticky RX error bits clear on RX reset.
# - interrupt_watermark_basic: Program TX and RX watermarks to small values, exercise FIFO level crossings, and verify intr_o assertion and INTR_STATE W1C clearing for watermark interrupts.
# - sticky_error_observation: Create RX parity and framing error scenarios using malformed serial frames, confirm STATUS sticky bits set, and verify they clear only via RX FIFO reset or full reset.
#
# Random tests:
# - csr_fuzz_with_scoreboard: Run constrained-random TL-UL CSR reads/writes across legal addresses with a mirrored model for register fields, reserved-bit masking, and W1C semantics, while checking single-cycle response behavior.
# - uart_loopback_random_payloads: With loopback enabled, send randomized byte streams under varied CTRL settings and compare TX-to-RX data integrity, FIFO levels, and interrupt side effects.
# - rx_serial_noise_and_error_injection: Drive randomized UART frames on uart_rx_i with occasional parity, stop-bit, and timing perturbations to exercise rx_parity_err, rx_frame_err, and overrun behavior.
# - watermark_and_reset_stress: Randomize FIFO_CTRL watermarks, issue intermittent FIFO resets, and verify interrupt re-arming, status consistency, and absence of deadlock across TX/RX activity.
