# CITADEL_SPI -- SPI Host Controller Specification

> **Disclaimer:** This RTL design is a modified version of an open-source IP block, created exclusively for this competition. It is not production-quality, not security-reviewed, and must not be used outside of this competition context.

---

## 1. Overview

CITADEL_SPI is a serial peripheral interface (SPI) host (master) controller. It generates the SPI clock (SCLK), drives chip-select lines, and transfers data to and from external SPI peripherals. The controller supports all four standard SPI modes via configurable clock polarity (CPOL) and clock phase (CPHA) settings.

Key features:

- Four active-low chip-select outputs (`csn_o[3:0]`), individually selectable.
- Configurable SCLK frequency via a 16-bit clock divider.
- Independent 16-entry transmit and receive FIFOs (8 bits per entry).
- Segment-based command interface: each SPI transaction consists of one or more segments, where each segment specifies a transfer direction, byte count, and chip-select management policy.
- A 4-entry command FIFO for queuing segment descriptors.
- Per-chip-select timing control for setup, hold, and inter-transfer idle periods.
- Four interrupt sources and an error reporting mechanism.

The controller connects to the system fabric through a TileLink-UL (TL-UL) bus interface.

---

## 2. Pin Interface

| Signal        | Width | Direction | Description                                    |
|---------------|-------|-----------|------------------------------------------------|
| `clk_i`       | 1     | Input     | System clock                                   |
| `rst_ni`      | 1     | Input     | Active-low asynchronous reset                  |
| `tl_i`        | struct | Input    | TL-UL request channel (host to device)         |
| `tl_i_ready`  | 1     | Output    | Device ready to accept TL-UL request           |
| `tl_o`        | struct | Output   | TL-UL response channel (device to host)        |
| `tl_o_ready`  | 1     | Input     | Host ready to accept TL-UL response            |
| `intr_o`      | 4     | Output    | Interrupt outputs (see Section 5)              |
| `alert_o`     | 1     | Output    | Alert output                                   |
| `sclk_o`      | 1     | Output    | SPI clock                                      |
| `csn_o`       | 4     | Output    | Chip-select outputs (active low)               |
| `mosi_o`      | 1     | Output    | Master-out / slave-in data                     |
| `miso_i`      | 1     | Input     | Master-in / slave-out data                     |

---

## 3. Functional Description

### 3.1 SPI Clock Generation

SCLK is derived from the system clock using a programmable 16-bit divider. The output frequency is:

    f_sclk = f_clk / (2 * (CLKDIV + 1))

where CLKDIV is the value programmed in the CONFIGOPTS register. The divider generates a symmetric (50% duty cycle) clock at the output.

When the SPI controller is idle (no active transaction), the SCLK output is held at the value determined by the CPOL setting. During a transaction, SCLK toggles at the programmed rate for the duration of data transfer.

### 3.2 SPI Modes (CPOL / CPHA)

The controller supports the four standard SPI modes through the CPOL and CPHA configuration bits:

| Mode | CPOL | CPHA | SCLK Idle | Data Output     | Data Sample     |
|------|------|------|-----------|-----------------|-----------------|
| 0    | 0    | 0    | Low       | Falling edge    | Rising edge     |
| 1    | 0    | 1    | Low       | Rising edge     | Falling edge    |
| 2    | 1    | 0    | High      | Rising edge     | Falling edge    |
| 3    | 1    | 1    | High      | Falling edge    | Rising edge     |

When CPHA is 0, the first data bit is driven onto MOSI at the leading edge of the chip-select assertion, before the first SCLK transition. The receiving side samples MISO on the first (leading) SCLK edge. When CPHA is 1, data is driven on the leading SCLK edge and sampled on the trailing SCLK edge.

### 3.3 Chip-Select Management

The controller provides four independent chip-select outputs. The active chip-select is selected by writing its index (0 through 3) to the CSID register. Only one chip-select may be active at a time. All chip-select lines are active-low: the selected line is driven low during a transaction and held high when idle.

Per-chip-select timing parameters are configured through the CONFIGOPTS register:

- **CSN_LEAD** (setup time): The number of half-SCLK periods between CS assertion and the first SCLK edge. This provides the peripheral with setup time before clocking begins.
- **CSN_TRAIL** (hold time): The number of half-SCLK periods between the last SCLK edge and CS deassertion. This ensures the peripheral captures the final data bit.
- **CSN_IDLE** (inter-CS delay): The minimum number of half-SCLK periods between CS deassertion and the next CS assertion. This parameter governs the gap between consecutive transactions.

When any of these timing values is zero, the minimum possible delay (a single half-SCLK period) is applied.

### 3.4 Segment-Based Transfers

SPI transactions are organized as a sequence of segments. Each segment is described by a command descriptor written to the COMMAND register, which is backed by a 4-entry command FIFO.

A segment descriptor contains the following fields:

- **Direction**: Specifies whether the segment is transmit-only, receive-only, or bidirectional.
- **Length**: The number of bytes in the segment, encoded as (byte_count - 1). A length value of 0 transfers one byte; a length of 511 transfers 512 bytes.
- **CSAAT** (Chip-Select Active After Transfer): When set, the chip-select line remains asserted after this segment completes, allowing the next segment to continue the same SPI transaction without deasserting CS.

For transmit segments, the controller pops data from the TX FIFO and shifts it out MSB-first onto MOSI, one byte at a time. For receive segments, the controller shifts in data from MISO and pushes completed bytes into the RX FIFO. During receive-only segments, the state of the MOSI output is not specified.

Bidirectional segments transfer data on both MOSI and MISO simultaneously. The controller clocks out bytes from the TX FIFO while simultaneously clocking in bytes from MISO.

### 3.5 Multi-Segment Transactions

When the CSAAT bit is set in a segment command, the chip-select remains asserted at the conclusion of that segment. The controller then proceeds to the next command in the command FIFO, if available. This enables complex multi-phase transactions (such as a write-address phase followed by a read-data phase) to be executed under a single chip-select assertion.

If CSAAT is set but the command FIFO is empty when the current segment completes, the controller stalls with the chip-select still asserted until the next command is written. The behavior during this stall -- particularly regarding SCLK state and any timeout mechanism -- is implementation-dependent.

When CSAAT is not set, the controller enters the CS hold phase after the segment completes, deasserts chip-select, waits for the idle period, and returns to the idle state (or processes the next command as a new transaction).

### 3.6 FIFO Behavior

The transmit FIFO is 16 entries deep, each 8 bits wide. Software writes data bytes to the TXDATA register to enqueue them. The controller dequeues bytes from the TX FIFO as they are needed during transmit or bidirectional segments.

The receive FIFO is also 16 entries deep and 8 bits wide. The controller enqueues received bytes into the RX FIFO during receive or bidirectional segments. Software reads received data from the RXDATA register.

FIFO levels are visible through the STATUS register (TXLVL and RXLVL fields), along with full and empty flags.

### 3.7 Error Conditions

Three error conditions are monitored:

- **TX Underflow**: A transmit or bidirectional segment requires a byte from the TX FIFO, but the FIFO is empty.
- **RX Overflow**: A received byte is ready to be pushed into the RX FIFO, but the FIFO is full.
- **Command Invalid**: A command is written to the COMMAND register when the command FIFO is already full.

Each error condition can be individually enabled or masked via the ERROR_ENABLE register. When an enabled error occurs, the corresponding bit in ERROR_STATUS is set. The cumulative error status feeds into the `error` interrupt.

ERROR_STATUS uses write-1-to-clear (W1C) semantics.

### 3.8 Output Enable

The `output_en` bit in the CTRL register controls whether the SPI output signals (SCLK, MOSI, and chip-select lines) are actively driven. When `output_en` is 0, the output signals should be considered in a high-impedance or inactive state. This bit is independent of the `spien` bit.

---

## 4. CSR Register Map

All registers are 32 bits wide. Byte address offsets are relative to the module base address.

| Offset | Name          | Access | Description                                                        |
|--------|---------------|--------|--------------------------------------------------------------------|
| 0x00   | CTRL          | RW     | SPI enable and output enable                                       |
| 0x04   | STATUS        | RO     | Controller and FIFO status                                         |
| 0x08   | CONFIGOPTS    | RW     | SPI mode and timing configuration                                  |
| 0x0C   | CSID          | RW     | Active chip-select index                                           |
| 0x10   | COMMAND       | WO     | Segment command descriptor (writes to command FIFO)                |
| 0x14   | TXDATA        | WO     | Transmit data (writes to TX FIFO)                                  |
| 0x18   | RXDATA        | RO     | Receive data (reads from RX FIFO)                                  |
| 0x1C   | ERROR_ENABLE  | RW     | Error condition enable mask                                        |
| 0x20   | ERROR_STATUS  | W1C    | Error condition status (write 1 to clear)                          |
| 0x24   | INTR_STATE    | W1C    | Interrupt status (write 1 to clear)                                |
| 0x28   | INTR_ENABLE   | RW     | Interrupt output enable                                            |
| 0x2C   | INTR_TEST     | RW     | Interrupt test injection                                           |

### 4.1 CTRL (0x00)

| Bits  | Field      | Reset | Description                          |
|-------|------------|-------|--------------------------------------|
| 0     | spien      | 0     | SPI controller enable                |
| 1     | output_en  | 0     | Drive SPI output signals             |
| 31:2  | reserved   | 0     | Reserved, reads as 0                 |

### 4.2 STATUS (0x04)

| Bits   | Field    | Description                                      |
|--------|----------|--------------------------------------------------|
| 0      | ready    | Controller is idle and ready for a new command    |
| 1      | active   | A transaction is currently in progress            |
| 2      | txfull   | TX FIFO is full                                   |
| 3      | txempty  | TX FIFO is empty                                  |
| 7:4    | txlvl    | Number of entries currently in the TX FIFO        |
| 8      | rxfull   | RX FIFO is full                                   |
| 9      | rxempty  | RX FIFO is empty                                  |
| 13:10  | rxlvl    | Number of entries currently in the RX FIFO        |
| 14     | cmdfull  | Command FIFO is full                              |
| 15     | cmdempty | Command FIFO is empty                             |
| 31:16  | reserved | Reserved, reads as 0                              |

### 4.3 CONFIGOPTS (0x08)

| Bits   | Field     | Reset | Description                                              |
|--------|-----------|-------|----------------------------------------------------------|
| 15:0   | clkdiv    | 0     | Clock divider: SCLK = clk / (2 * (clkdiv + 1))         |
| 19:16  | csn_lead  | 0     | CS-to-SCLK setup time (in half-SCLK periods)            |
| 23:20  | csn_trail | 0     | SCLK-to-CS-deassert hold time (in half-SCLK periods)    |
| 27:24  | csn_idle  | 0     | Minimum inter-CS idle time (in half-SCLK periods)        |
| 28     | cpol      | 0     | Clock polarity (0 = idle low, 1 = idle high)            |
| 29     | cpha      | 0     | Clock phase (0 = sample on leading edge)                 |
| 31:30  | reserved  | 0     | Reserved                                                 |

### 4.4 CSID (0x0C)

| Bits  | Field  | Reset | Description                              |
|-------|--------|-------|------------------------------------------|
| 1:0   | csid   | 0     | Chip-select index (0 to 3)               |
| 31:2  | reserved | 0   | Reserved                                 |

### 4.5 COMMAND (0x10)

| Bits   | Field     | Description                                              |
|--------|-----------|----------------------------------------------------------|
| 8:0    | len       | Segment length in bytes minus 1 (0 = 1 byte)            |
| 10:9   | speed     | Reserved for future use                                  |
| 11     | csaat     | Keep CS asserted after segment (1 = hold CS active)      |
| 13:12  | direction | 0 = TX only, 1 = RX only, 2 = bidirectional             |
| 31:14  | reserved  | Reserved                                                 |

Writes to COMMAND when the controller is disabled (spien = 0) are accepted into the command FIFO but the controller does not begin processing them until the SPI enable is asserted.

### 4.6 TXDATA (0x14)

| Bits  | Field | Description                                |
|-------|-------|--------------------------------------------|
| 7:0   | data  | Byte written into the TX FIFO              |
| 31:8  | reserved | Ignored on write                        |

### 4.7 RXDATA (0x18)

| Bits  | Field | Description                                |
|-------|-------|--------------------------------------------|
| 7:0   | data  | Byte read from the RX FIFO                 |
| 31:8  | reserved | Reads as 0                              |

### 4.8 ERROR_ENABLE (0x1C)

| Bits  | Field       | Reset | Description                           |
|-------|-------------|-------|---------------------------------------|
| 0     | underflow   | 0     | Enable TX underflow error reporting   |
| 1     | overflow    | 0     | Enable RX overflow error reporting    |
| 2     | cmd_invalid | 0     | Enable command-invalid error reporting|
| 31:3  | reserved    | 0     | Reserved                              |

### 4.9 ERROR_STATUS (0x20)

| Bits  | Field       | Reset | Description                           |
|-------|-------------|-------|---------------------------------------|
| 0     | underflow   | 0     | TX underflow occurred (W1C)           |
| 1     | overflow    | 0     | RX overflow occurred (W1C)            |
| 2     | cmd_invalid | 0     | Invalid command write occurred (W1C)  |
| 31:3  | reserved    | 0     | Reserved                              |

### 4.10 INTR_STATE (0x24), INTR_ENABLE (0x28), INTR_TEST (0x2C)

| Bit | Interrupt     | Description                                       |
|-----|---------------|---------------------------------------------------|
| 0   | spi_done      | An SPI transaction has completed                  |
| 1   | rx_watermark   | RX FIFO level has reached the watermark threshold |
| 2   | tx_watermark   | TX FIFO level has fallen to the watermark threshold|
| 3   | error         | An enabled error condition has been detected       |

INTR_STATE bits are set by hardware events and cleared by software writing 1 to the corresponding bit. INTR_ENABLE masks which interrupts drive the `intr_o` outputs. INTR_TEST allows software to inject interrupt events for diagnostic purposes.

The watermark thresholds for `rx_watermark` and `tx_watermark` are fixed within the implementation and are not software-configurable.

### CSR Access Notes

- Writes to read-only registers (STATUS, RXDATA) are silently ignored.
- Reads from write-only registers (COMMAND, TXDATA) return 0.
- Accesses to reserved or unimplemented addresses return 0 on read and are ignored on write.

---

## 5. Timing Considerations

- The TL-UL interface responds in a single cycle for all CSR accesses.
- SCLK generation begins after the CS setup phase completes.
- Data bytes are shifted MSB-first on the SPI bus.
- FIFO level updates (STATUS register) reflect the state at the time of the register read; they are not pipelined.
- Interrupt outputs are combinational functions of INTR_STATE and INTR_ENABLE.

---

## 6. Alert Behavior

The `alert_o` signal is reserved for fatal internal error conditions. Under normal operation, `alert_o` remains deasserted. The specific conditions that may trigger an alert are related to internal consistency checks and are not enumerated here.
