# Verification Plan

## Features
- TL-UL CSR access with single-cycle response and unmapped-address error handling
- UART control register programming for tx_enable, rx_enable, baud_divisor, parity_mode, stop_bits, and loopback_en
- TX FIFO push/pop behavior through TXDATA and RXDATA
- RX FIFO status reporting including empty/full/level and sticky error bits
- FIFO flush control via FIFO_CTRL for TX and RX paths
- Interrupt generation and W1C handling for watermark and error conditions
- Loopback-based end-to-end serial data path validation
- Reset behavior and CSR default value checking
- Reserved-bit read-as-zero and write-ignore behavior
- Basic protocol robustness for TL-UL read/write sequencing and backpressure tolerance

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_and_csr_smoke: Verify reset defaults for all 8 CSRs, reserved bits read as zero, write-ignore behavior on reserved fields, and basic TL-UL read/write access to CTRL, STATUS, TXDATA, RXDATA, FIFO_CTRL, and interrupt registers.
- tlul_unmapped_address_error: Issue reads and writes to unmapped addresses and confirm error responses while preserving DUT stability and subsequent legal access functionality.
- ctrl_programming_sweep: Program representative CTRL combinations for tx_enable/rx_enable, baud_divisor, parity_mode, stop_bits, and loopback_en; confirm register readback and no protocol or CSR decode issues.
- tx_fifo_fill_and_full_status: Write TXDATA until TX FIFO reaches full, verify tx_fifo_level and tx_fifo_full transitions, and confirm additional writes are handled according to peripheral behavior without corrupting status.
- rx_fifo_read_and_empty_status: Inject receive bytes through uart_rx_i or loopback, read RXDATA until empty, and verify rx_fifo_level, rx_fifo_empty, and data ordering.
- loopback_basic_data_path: Enable loopback and transmit a small set of bytes through TXDATA, then verify the same bytes are observed on RXDATA with correct ordering and status updates.
- fifo_flush_clears_levels: Populate TX and RX FIFOs, assert tx_fifo_rst and rx_fifo_rst independently via FIFO_CTRL, and verify FIFO levels return to empty and sticky RX error bits clear on RX reset.
- interrupt_watermark_basic: Program TX and RX watermarks to small values, exercise FIFO level crossings, and verify intr_o assertion and INTR_STATE W1C clearing for watermark interrupts.
- sticky_error_observation: Create RX parity and framing error scenarios using malformed serial frames, confirm STATUS sticky bits set, and verify they clear only via RX FIFO reset or full reset.

## Random Tests
- csr_fuzz_with_scoreboard: Run constrained-random TL-UL CSR reads/writes across legal addresses with a mirrored model for register fields, reserved-bit masking, and W1C semantics, while checking single-cycle response behavior.
- uart_loopback_random_payloads: With loopback enabled, send randomized byte streams under varied CTRL settings and compare TX-to-RX data integrity, FIFO levels, and interrupt side effects.
- rx_serial_noise_and_error_injection: Drive randomized UART frames on uart_rx_i with occasional parity, stop-bit, and timing perturbations to exercise rx_parity_err, rx_frame_err, and overrun behavior.
- watermark_and_reset_stress: Randomize FIFO_CTRL watermarks, issue intermittent FIFO resets, and verify interrupt re-arming, status consistency, and absence of deadlock across TX/RX activity.

## Risk Areas
- UART timing, baud divisor, and oversampling behavior (high): Most likely source of functional mismatch because bit timing, 16x oversampling, and divisor edge cases are implementation-sensitive and can break end-to-end data transfer.
- FIFO boundary conditions and overflow/underflow handling (high): 32-byte FIFO depth, full/empty transitions, and write/read behavior at boundaries are common defect sources and directly affect data integrity.
- Interrupt generation, W1C semantics, and watermark re-arming (high): Spec explicitly notes implementation-defined re-arming behavior, so this area needs characterization and is prone to mismatches between RTL and expectations.
- Sticky error bits and reset interactions (medium): rx_overrun, rx_parity_err, and rx_frame_err have nontrivial clear conditions and can easily be implemented inconsistently across FIFO reset and global reset paths.
- TL-UL protocol compliance and unmapped access errors (medium): Bus decode and response correctness are essential but lower risk than core UART datapath; still required for a stable verification environment.
- Reserved field masking and CSR readback fidelity (low): Usually straightforward, but important for completeness and to catch decode bugs in the 8-register CSR block.
