# Verification Plan

## Features
- TL-UL CSR access with single-cycle response
- UART full-duplex TX/RX datapaths
- 32-byte TX FIFO and 32-byte RX FIFO
- Programmable baud divisor, parity, stop bits, and loopback
- Status register with sticky error reporting
- FIFO flush control and watermark-based interrupts
- Interrupt state/enable/clear behavior
- Reset behavior and reserved-bit handling
- Unmapped address error response
- Basic alert observation for fatal integrity conditions

## Coverage Goals
- Line: 85%
- Branch: 75%
- Functional: 85%

## Directed Tests
- reset_smoke_csr_map: Verify reset values, TL-UL read/write access, unmapped address error response, and reserved-bit read-as-zero behavior across the 8 CSRs.
- ctrl_programming_and_loopback_smoke: Program CTRL fields for TX/RX enable, baud divisor, parity, stop bits, and loopback; confirm register readback and basic loopback data transfer.
- tx_fifo_basic_push_and_status: Write a small burst to TXDATA, confirm TX FIFO level/empty/full status transitions, and ensure writes to reserved TXDATA bits are ignored.
- rx_fifo_basic_receive_and_status: Drive uart_rx_i with a valid frame, confirm RXDATA readout, RX FIFO level/empty status transitions, and basic receive enable gating.
- fifo_flush_controls: Assert TX and RX FIFO reset bits in FIFO_CTRL, verify self-clearing behavior, FIFO emptying, and clearing of sticky RX error bits via RX FIFO reset.
- watermark_interrupts: Program TX/RX watermarks, exercise FIFO level crossings, and verify INTR_STATE/INTR_ENABLE/INTR_TEST behavior for watermark interrupts.
- sticky_error_capture: Inject parity and framing errors on RX, verify STATUS sticky bits set correctly, and confirm they persist until RX FIFO reset or full reset.
- fifo_boundary_conditions: Fill TX and RX FIFOs to capacity, verify full flags, overrun handling on RX overflow, and safe behavior when writing TXDATA while full.

## Random Tests
- tlul_csr_fuzzer: Constrained-random TL-UL reads/writes across valid CSR addresses, reserved bits, and unmapped addresses with scoreboard checking of readback, side effects, and error responses.
- uart_loopback_stream_random: Enable loopback and run randomized byte streams with varying parity, stop bits, and baud divisors to stress TX/RX alignment and FIFO interactions.
- rx_protocol_noise_injection: Randomly inject malformed UART frames, parity mismatches, and stop-bit violations to exercise sticky error paths and RX FSM recovery.
- watermark_and_interrupt_stress: Randomize FIFO watermark settings and traffic patterns to validate interrupt assertion, clearing, and re-arming behavior under load.
- reset_during_activity: Apply asynchronous reset during active TX/RX and TL-UL traffic to verify clean recovery, FIFO flush, and no stuck interrupts or alerts.

## Risk Areas
- UART baud timing and oversampling (high): Most likely source of functional mismatch due to divisor interpretation, 16x sampling, and undefined divisor-zero behavior.
- FIFO boundary and overflow/underflow behavior (high): 32-byte FIFOs with full/empty flags, overrun sticky status, and write-while-full behavior are common defect points.
- Interrupt generation and W1C handling (high): Watermark interrupts, state/enable/clear semantics, and re-arming behavior are implementation-sensitive and high risk.
- Sticky error reporting and reset clearing (medium): Parity and framing error bits must persist correctly and clear only via FIFO reset or full reset.
- TL-UL protocol compliance (medium): Single-cycle response, unmapped address errors, and reserved-bit handling are straightforward but essential for integration.
- Loopback mode data path coupling (medium): Internal routing between TX and RX can hide issues in external pin handling or create unintended combinational paths.
- Alert output behavior (low): Fatal alert conditions are likely rare and may be difficult to fully characterize within the 60-minute budget.
