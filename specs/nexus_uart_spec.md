# NEXUS_UART -- Full-Duplex UART Controller

> **Disclaimer:** This RTL design is a modified version of an open-source IP block, created exclusively for this competition. It is not production-quality, not security-reviewed, and must not be used outside of this competition context.

---

## 1. Overview

NEXUS_UART is a full-duplex universal asynchronous receiver/transmitter with configurable baud rate, parity, and stop-bit options. It provides independent transmit and receive data paths, each backed by a 32-byte synchronous FIFO, and exposes a standard TileLink-UL (TL-UL) register interface for host access. The design supports loopback mode for self-test and generates maskable interrupts for a variety of status conditions.

The baud rate is set through a 16-bit programmable divisor applied to the system clock. Receive-side clock recovery uses 16x oversampling with mid-bit sampling, consistent with standard UART practice.

## 2. Block-Level Architecture

```
                  TL-UL Bus
                     |
              +------+------+
              |  CSR Block  |
              +--+-------+--+
                 |       |
          +------+--+ +--+------+
          | TX Path | | RX Path |
          +----+----+ +----+----+
               |            |
          +----+----+ +----+----+
          | TX FIFO | | RX FIFO |
          | (32B)   | | (32B)   |
          +----+----+ +----+----+
               |            |
          +----+----+ +----+----+
          | TX FSM  | | RX FSM  |
          +----+----+ +----+----+
               |            |
            uart_tx_o    uart_rx_i
```

When loopback is enabled, the transmit serial output is internally routed to the receive serial input, bypassing the external pins.

## 3. Signal Interface

| Signal      | Direction | Width | Description                              |
|-------------|-----------|-------|------------------------------------------|
| clk_i       | input     | 1     | System clock                             |
| rst_ni      | input     | 1     | Active-low asynchronous reset            |
| tl_i        | input     | packed| TL-UL A-channel request (tl_a_pkt_t)    |
| tl_i_ready  | output    | 1     | Backpressure for A-channel               |
| tl_o        | output    | packed| TL-UL D-channel response (tl_d_pkt_t)   |
| tl_o_ready  | input     | 1     | Downstream ready for D-channel           |
| uart_tx_o   | output    | 1     | Serial transmit data                     |
| uart_rx_i   | input     | 1     | Serial receive data                      |
| intr_o      | output    | 7     | Interrupt vector (active-high)           |
| alert_o     | output    | 1     | Fatal alert (FIFO integrity, etc.)       |

The TL-UL interface follows the simplified protocol defined in `dv_common_pkg`. A-channel transactions with `a_opcode` of `PutFullData` (0) perform writes; transactions with `a_opcode` of `Get` (4) perform reads. The device always responds in the same cycle the request is accepted (single-cycle response latency). Requests to unmapped addresses receive an error response.

## 4. Register Map

Base offset: 0x00. All registers are 32 bits wide; undefined bit fields read as zero and writes are ignored.

### 4.1 CTRL (0x00) -- Control Register [RW]

| Bits   | Field          | Reset | Description                                              |
|--------|----------------|-------|----------------------------------------------------------|
| 0      | tx_enable      | 0     | Enable transmit path                                     |
| 1      | rx_enable      | 0     | Enable receive path                                      |
| 17:2   | baud_divisor   | 0     | Baud rate divisor (system_clk / (baud_rate * 16))        |
| 19:18  | parity_mode    | 0     | 00: none, 01: even parity, 10: odd parity, 11: reserved |
| 20     | stop_bits      | 0     | 0: 1 stop bit, 1: 2 stop bits                           |
| 21     | loopback_en    | 0     | Connect TX output to RX input internally                 |
| 31:22  | --             | --    | Reserved                                                 |

The baud_divisor value determines the bit period. The transmitter counts system clock cycles from 0 up to the full divisor value to generate bit timing. The receiver divides this further by 16 for oversampling. A divisor value of 0 is undefined behavior; the resulting baud rate when divisor is set to 0 is not specified.

### 4.2 STATUS (0x04) -- Status Register [RO, mixed]

| Bits   | Field          | Access | Description                                          |
|--------|----------------|--------|------------------------------------------------------|
| 0      | tx_fifo_empty  | RO     | TX FIFO contains no entries                          |
| 1      | tx_fifo_full   | RO     | TX FIFO is at capacity                               |
| 2      | rx_fifo_empty  | RO     | RX FIFO contains no entries                          |
| 3      | rx_fifo_full   | RO     | RX FIFO is at capacity                               |
| 9:4    | tx_fifo_level  | RO     | Number of entries currently in TX FIFO               |
| 15:10  | rx_fifo_level  | RO     | Number of entries currently in RX FIFO               |
| 16     | rx_overrun     | RO     | RX FIFO was full when new data arrived (sticky)      |
| 17     | rx_parity_err  | RO     | Most recent RX frame had parity mismatch (sticky)    |
| 18     | rx_frame_err   | RO     | Most recent RX frame had invalid stop bit (sticky)   |
| 31:19  | --             | --     | Reserved                                             |

Sticky error bits in STATUS are cleared by resetting the corresponding RX FIFO via FIFO_CTRL, or by a full device reset. They are not independently clearable.

### 4.3 TXDATA (0x08) -- Transmit Data Register [WO]

| Bits  | Field  | Description                            |
|-------|--------|----------------------------------------|
| 7:0   | data   | Byte to push into the TX FIFO          |
| 31:8  | --     | Reserved (writes ignored)              |

Writing to TXDATA when the TX FIFO is full follows standard UART peripheral practice. Software should check STATUS.tx_fifo_full before writing.

### 4.4 RXDATA (0x0C) -- Receive Data Register [RO]

| Bits  | Field  | Description                            |
|-------|--------|----------------------------------------|
| 7:0   | data   | Byte popped from the RX FIFO on read   |
| 31:8  | --     | Reserved (reads as zero)               |

Reading RXDATA when the RX FIFO is empty returns unspecified data. Software should check STATUS.rx_fifo_empty before reading.

### 4.5 FIFO_CTRL (0x10) -- FIFO Control Register [RW]

| Bits   | Field          | Reset | Description                                       |
|--------|----------------|-------|---------------------------------------------------|
| 4:0    | tx_watermark   | 1     | TX FIFO watermark level for interrupt generation   |
| 9:5    | rx_watermark   | 1     | RX FIFO watermark level for interrupt generation   |
| 10     | tx_fifo_rst    | 0     | Write 1 to flush the TX FIFO (self-clearing)       |
| 11     | rx_fifo_rst    | 0     | Write 1 to flush the RX FIFO (self-clearing)       |
| 31:12  | --             | --    | Reserved                                           |

The TX watermark interrupt fires when the TX FIFO level drops to or below the programmed watermark. The RX watermark interrupt fires when the RX FIFO level rises to or above the programmed watermark. The precise re-arming behavior of watermark interrupts after software clears them is implementation-defined; teams should characterize the actual behavior.

### 4.6 INTR_STATE (0x14) -- Interrupt State Register [RW, W1C]

| Bit | Field          | Description                                                |
|-----|----------------|------------------------------------------------------------|
| 0   | tx_watermark   | TX FIFO level is at or below programmed watermark          |
| 1   | rx_watermark   | RX FIFO level is at or above programmed watermark          |
| 2   | tx_empty       | TX FIFO has become empty                                   |
| 3   | rx_overflow    | Data was lost due to RX FIFO overflow                      |
| 4   | rx_frame_err   | Received frame had invalid stop bit                        |
| 5   | rx_parity_err  | Received frame had parity error                            |
| 6   | rx_timeout     | RX line idle for extended period after activity             |

All bits are level-sensitive internally and latched. Once set, a bit remains set until cleared by writing 1 to that bit position (W1C). Writing 0 to a bit has no effect.

### 4.7 INTR_ENABLE (0x18) -- Interrupt Enable Register [RW]

Each bit enables the corresponding INTR_STATE bit to propagate to the `intr_o` output. When a bit is 0, the corresponding interrupt is masked but the state bit in INTR_STATE still reflects the underlying condition.

### 4.8 INTR_TEST (0x1C) -- Interrupt Test Register [WO]

Writing a 1 to any bit position forces the corresponding INTR_STATE bit to set, regardless of the actual hardware condition. Used for interrupt controller integration testing. Read returns 0.

## 5. Transmit Path

### 5.1 Baud Rate Generation

The transmit baud counter counts system clock cycles from 0 to the programmed baud_divisor value. When the counter reaches the divisor, it wraps to 0 and the TX FSM advances to the next bit.

### 5.2 TX FSM

The transmitter operates with the following state sequence per frame:

**IDLE**: uart_tx_o is held high. When tx_enable is asserted and the TX FIFO is non-empty, a byte is popped from the FIFO and the FSM transitions to START.

**START**: uart_tx_o is driven low for one bit period.

**DATA[0] through DATA[7]**: The 8 data bits are transmitted LSB first, each held for one bit period.

**PARITY**: If parity_mode is not "none," the parity bit is transmitted. Even parity is the XOR reduction of the 8 data bits; odd parity is its complement. This state is skipped when parity is disabled.

**STOP**: uart_tx_o is driven high for one or two bit periods depending on the stop_bits configuration. After the final stop bit, the FSM returns to IDLE.

If the TX FIFO contains another byte when the FSM returns to IDLE, transmission of the next frame should begin with minimal inter-frame gap. The exact behavior of back-to-back framing is left to standard practice.

## 6. Receive Path

### 6.1 Oversampling and Clock Recovery

The receiver operates at 16 times the baud rate, using the baud_divisor divided by 16 to set the oversampling tick period. The receiver performs mid-bit sampling to determine each bit value. The exact sample point within the 16x window is at the nominal center of the bit period.

### 6.2 RX FSM

**IDLE**: The receiver waits for a falling edge on the RX input (start of start bit). rx_enable must be asserted.

**START_DET**: After detecting the falling edge, the receiver waits until the mid-point of the start bit and verifies it is still low. If the line has returned high, this is treated as a glitch and the FSM returns to IDLE.

**SAMPLE_DATA[0] through SAMPLE_DATA[7]**: Each data bit is sampled at the mid-bit point, LSB first.

**CHECK_PARITY**: If parity is enabled, the parity bit is sampled and compared against the expected value. A mismatch sets the rx_parity_err status and interrupt.

**STOP_CHECK**: The stop bit is sampled. A low value during the stop bit constitutes a framing error. When 2 stop bits are configured, both must be checked. After the stop bit(s), if no errors occurred, the received byte is pushed into the RX FIFO. If the FIFO is full at this point, an overflow condition occurs.

### 6.3 Error Handling

- **Parity error**: Set when the sampled parity bit does not match the calculated expected parity. Sticky until RX FIFO reset.
- **Framing error**: Set when the stop bit samples as low. The frame's data may or may not be written to the FIFO; behavior follows common UART implementations.
- **Overflow**: When the RX FIFO is full and a new byte completes reception, the incoming data is discarded and the overflow status is set.

### 6.4 RX Timeout

The receiver monitors idle time on the RX line after activity has been observed. If the line remains idle (high) for an extended period following the last received byte, an rx_timeout interrupt is generated. The timeout period follows standard UART practice and fires after the line has been idle long enough to suggest the transmitting device has stopped sending. The exact timeout threshold is not exposed to software as a configurable register field.

## 7. Interrupts

NEXUS_UART generates 7 interrupt sources, output as a packed 7-bit vector on `intr_o[6:0]`. Each interrupt source has corresponding bits in INTR_STATE, INTR_ENABLE, and INTR_TEST.

The output vector is computed as: `intr_o = intr_state & intr_enable`.

Interrupt sources are level-based internally. The hardware continuously evaluates the interrupt conditions and updates internal status. INTR_STATE latches any assertion of these conditions. Software clears an interrupt by writing 1 to the corresponding bit in INTR_STATE.

Note that because some interrupt sources are level-sensitive (e.g., tx_watermark, rx_watermark), clearing the INTR_STATE bit while the underlying condition persists may cause the bit to reassert. The timing of reassertion relative to the W1C write is not precisely specified.

## 8. Loopback Mode

When CTRL.loopback_en is set, the serial output of the transmitter is internally connected to the receiver input. The external uart_tx_o pin continues to reflect the transmitted data, but uart_rx_i is ignored. This mode is intended for self-test and bringup diagnostics. Both TX and RX paths must be enabled for loopback to function correctly. Behavior when only one path is enabled during loopback is not defined.

## 9. Alert Output

The alert_o signal is reserved for fatal hardware errors such as FIFO pointer corruption or internal state machine errors. Under normal operation, alert_o should remain deasserted.

## 10. Reset Behavior

On assertion of rst_ni (active-low), all registers return to their reset values, both FIFOs are flushed, FSMs return to IDLE, and uart_tx_o is driven high. The reset is asynchronous and takes effect regardless of clock state.
