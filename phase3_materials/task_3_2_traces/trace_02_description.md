# Trace 02: Nexus UART — TX FIFO Pointer Corruption on Overflow

## Failing Assertion

```
ASSERTION FAILED: assert_tx_fifo_data_integrity
  Location: nexus_uart_sva.sv:78
  Message: "TX FIFO read data must match the data written at the same FIFO index"
  Failure time: cycle 500
```

## Spec Requirement

From the Nexus UART Specification, Section 2.3.1:

> **TX FIFO:** The transmit FIFO is 32 entries deep. When the FIFO is full
> (tx_fifo_full = 1), writes to TXDATA shall be silently discarded. The FIFO
> shall not corrupt existing entries on overflow. The write pointer shall not
> advance when the FIFO is full.

## Test Scenario

1. Configure UART: tx_en=1, baud=434, no parity, 1 stop bit
2. Fill TX FIFO to capacity (32 entries) with sequential data 0x00-0x1F
3. Attempt to write 3 additional bytes (0x80, 0x81, 0x82) to trigger overflow
4. Read back TX FIFO contents by monitoring transmitted data on uart_tx_o
5. Verify all 32 original entries are transmitted in order without corruption

## Observed Behavior

The first 32 bytes are loaded correctly. When the 33rd byte (0x80) is written
to the full FIFO, the write pointer does NOT advance (correct), but the FIFO
memory at index 0 is overwritten with 0x80. The transmitted data shows byte 0
as 0x80 instead of the expected 0x00.

The corruption occurs because the memory write `tx_fifo_mem[tx_wptr[4:0]] <= tx_fifo_wdata`
executes whenever `tx_fifo_push` is asserted, but the write pointer is at index
0 (wrapped: tx_wptr = 6'b100000, so tx_wptr[4:0] = 5'b00000). The full-check
only gates the pointer increment, not the memory write.

## Signal Trace File

See `trace_02_signals.csv` for cycle-by-cycle signal values.
Key signals:
- `tx_wptr[5:0]` — TX FIFO write pointer (6-bit with wrap)
- `tx_rptr[5:0]` — TX FIFO read pointer
- `tx_fifo_full` — FIFO full flag
- `tx_fifo_push` — write request to FIFO
- `tx_fifo_wdata[7:0]` — data being written
- `tx_fifo_rdata[7:0]` — data being read for transmission
