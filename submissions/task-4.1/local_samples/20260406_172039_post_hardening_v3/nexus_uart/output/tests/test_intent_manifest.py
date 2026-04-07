# Auto-generated test intent summary
#
# Directed tests:
# - reset_smoke_csr_map: Apply reset, verify all documented reset values, reserved bits read as zero, and basic TL-UL read/write access to CTRL, STATUS, TXDATA, RXDATA, FIFO_CTRL, and interrupt state registers.
# - tlul_unmapped_address_error: Issue reads and writes to unmapped addresses and confirm error response behavior without side effects on valid CSRs.
# - ctrl_programming_sanity: Program tx_enable, rx_enable, baud_divisor, parity_mode, stop_bits, and loopback_en individually and in combination, then read back CTRL to confirm writable fields and reserved-bit masking.
# - tx_fifo_push_level_status: Write a small sequence of bytes to TXDATA, verify TX FIFO level increments, empty/full flags update correctly, and TXDATA reserved bits are ignored.
# - rx_fifo_pop_level_status: Inject receive bytes on uart_rx_i, verify RX FIFO level increments, read RXDATA to pop bytes, and confirm empty/full flags update correctly.
# - loopback_basic_data_path: Enable loopback with TX and RX enabled, transmit a byte stream, and verify received data matches transmitted data across multiple byte values.
# - parity_modes_even_odd_none: Run loopback transfers under no parity, even parity, and odd parity settings to confirm successful reception in supported modes and characterize reserved parity mode behavior if exercised.
# - stop_bits_1_and_2: Verify transmit/receive operation with 1 stop bit and 2 stop bits, ensuring no functional regression in loopback and external receive stimulus.
# - fifo_watermark_interrupts: Program TX and RX watermarks, drive FIFO levels across thresholds, and verify interrupt assertion, W1C clearing, and re-arming behavior.
# - fifo_reset_and_sticky_error_clear: Assert TX and RX FIFO reset bits, confirm FIFOs flush, and verify STATUS sticky error bits clear only via RX FIFO reset or full reset.
# - rx_overrun_characterization: Overfill RX FIFO with external stimulus to provoke overrun, then confirm STATUS.rx_overrun sets and remains sticky until RX FIFO reset.
# - rx_parity_and_frame_error_characterization: Inject malformed UART frames to provoke parity and stop-bit errors, then confirm STATUS sticky error bits set and are observable through CSR reads.
#
# Random tests:
# - tlul_csr_fuzz_smoke: Run constrained-random TL-UL reads and writes across valid CSR addresses with scoreboarding for readback, write-ignore, and error responses, keeping runtime bounded to a short smoke window.
# - uart_loopback_random_payloads: Randomize payload bytes, burst lengths, and inter-byte gaps in loopback mode to stress TX/RX FIFOs, FSM transitions, and data ordering.
# - uart_random_config_matrix: Randomly sweep baud_divisor, parity_mode, stop_bits, and enable combinations within legal ranges while performing short loopback transfers to catch configuration-dependent issues.
# - fifo_pressure_random: Apply randomized TX writes and RX injections near FIFO capacity to exercise full/empty transitions, watermark interrupts, and overrun handling under pressure.
