# Verification Plan

## Features
- TL-UL CSR access with single-cycle response checking
- UART control register programming: tx_enable, rx_enable, baud_divisor, parity_mode, stop_bits, loopback_en
- STATUS register readback and sticky error observation
- TXDATA write path and TX FIFO fill/empty behavior
- RXDATA read path and RX FIFO drain behavior
- FIFO_CTRL watermark programming and FIFO reset behavior
- Interrupt state/enable/clear behavior for watermark and error conditions
- Loopback functional path from uart_tx_o to uart_rx_i
- Parity and stop-bit configuration coverage
- Reset behavior and post-reset default state
- Unmapped address error response
- FIFO overflow/underflow and sticky error characterization
- Basic UART timing sanity across a small set of baud divisors

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_csr_map: Verify reset defaults for all 8 CSRs, TL-UL read/write access, reserved-bit behavior, and unmapped address error response.
- ctrl_programming_sanity: Program CTRL with representative combinations of tx_enable, rx_enable, parity_mode, stop_bits, and baud_divisor; confirm readback and no protocol errors.
- tx_fifo_basic_push_pop: Write a small sequence to TXDATA, observe STATUS level/empty/full transitions, and confirm TX FIFO accepts data when enabled.
- rx_loopback_basic: Enable loopback, transmit a few bytes, and verify they are received in order through RXDATA with matching STATUS updates.
- fifo_watermark_interrupts: Program TX/RX watermarks, drive FIFO levels across thresholds, and verify INTR_STATE assertion and W1C clearing behavior.
- fifo_reset_and_sticky_error_clear: Force RX overrun or parity/frame error conditions if achievable, then verify FIFO_CTRL reset clears sticky STATUS bits and flushes FIFOs.
- parity_stopbit_matrix_smoke: Exercise even/odd/no parity and 1/2 stop-bit settings with a minimal set of loopback frames to confirm no obvious framing failures.
- baud_divisor_sweep_small: Run a short sweep of representative baud_divisor values, including a mid-range value and a corner value near minimum legal operation, to validate timing robustness.

## Random Tests
- tlul_csr_fuzz: Randomize legal CSR reads/writes, reserved-bit writes, and occasional unmapped accesses while checking TL-UL response integrity and register invariants.
- uart_loopback_fifo_stress: Randomly generate TX bursts, RX consumption delays, and loopback enable patterns to stress FIFO occupancy, watermark interrupts, and data ordering.
- config_mixed_stress: Randomly vary CTRL and FIFO_CTRL settings between short traffic bursts to expose state-machine corner cases across TX, RX, and interrupt logic.

## Risk Areas
- Loopback data path and RX sampling (high): Highest functional risk because TX-to-RX internal routing, oversampling, and mid-bit sampling can fail silently while CSR access still passes.
- FIFO boundary conditions and overflow/underflow (high): 32-byte FIFOs plus watermark logic create off-by-one and full/empty transition risks; these are common sources of latent bugs.
- Interrupt generation and W1C behavior (high): Seven interrupt outputs with watermark and error sources require correct set/clear semantics and are likely to have implementation-specific corner cases.
- Parity and stop-bit configuration (medium): Multiple framing modes increase FSM branch space and can expose protocol mismatches, especially in loopback.
- Baud divisor timing edge cases (medium): Programmable divisor and 16x oversampling can misbehave at small or unusual divisors; full exhaustive timing is out of budget.
- Sticky error clearing via FIFO reset (medium): STATUS sticky bits depend on reset side effects rather than direct clear, which is easy to implement incorrectly.
- TL-UL unmapped address and reserved-bit handling (low): Lower functional risk but important for bus compliance and CSR robustness; straightforward to cover quickly.
