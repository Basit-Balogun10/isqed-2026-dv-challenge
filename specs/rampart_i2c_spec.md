# RAMPART_I2C -- I2C Host/Target Controller

> **Disclaimer:** This RTL design is a modified version of an open-source IP block, created exclusively for this competition. It is not production-quality, not security-reviewed, and must not be used outside of this competition context.

---

## 1. Overview

RAMPART_I2C is a dual-role I2C controller capable of operating as both a bus host (master) and a bus target (slave). It supports standard-mode (100 kHz), fast-mode (400 kHz), and fast-mode-plus (1 MHz) operation, with all timing parameters exposed as programmable CSRs to accommodate a range of system clock frequencies.

The controller connects to the system fabric through a TileLink-UL (TL-UL) bus interface and drives the I2C bus using open-drain signaling. Two independent FSMs manage host-initiated and target-initiated transactions. FIFOs decouple software from real-time bus activity: a 64-entry format FIFO queues host-mode bus commands, a 64-entry RX FIFO captures data received in host mode, a 64-entry TX FIFO holds data for target-mode transmissions, and a 64-entry acquire FIFO captures data received in target mode.

Multi-master arbitration is supported per the I2C specification. The controller monitors the bus for arbitration loss and responds accordingly.

---

## 2. Block-Level Architecture

```
                   TL-UL Bus
                      |
               +------+------+
               |  CSR Block  |
               +--+--+--+--+-+
                  |  |  |  |
          +-------+  |  |  +--------+
          |          |  |            |
     +----+----+ +--+--+--+ +------+------+
     |Format   | | RX     | | TX   | ACQ  |
     |FIFO(64) | | FIFO   | | FIFO | FIFO |
     |         | | (64)   | | (64) | (64) |
     +----+----+ +--+-----+ +--+---+--+---+
          |          |          |       |
     +----+----------+----+ +--+-------+--+
     |   Host FSM         | | Target FSM  |
     +--------+-----------+ +------+------+
              |                    |
         +----+--------------------+----+
         |     SCL/SDA Open-Drain       |
         |     Bus Interface            |
         +------------------------------+
```

The host and target FSMs share the physical SCL and SDA lines. Only one role actively drives the bus at any time; the controller arbitrates internally based on which mode is enabled and the current bus state.

---

## 3. Signal Interface

| Signal       | Direction | Width  | Description                                 |
|--------------|-----------|--------|---------------------------------------------|
| `clk_i`      | Input     | 1      | System clock                                |
| `rst_ni`     | Input     | 1      | Active-low asynchronous reset               |
| `tl_i`       | Input     | packed | TL-UL A-channel request (tl_a_pkt_t)       |
| `tl_i_ready` | Output    | 1      | Backpressure for A-channel                  |
| `tl_o`       | Output    | packed | TL-UL D-channel response (tl_d_pkt_t)      |
| `tl_o_ready` | Input     | 1      | Downstream ready for D-channel              |
| `scl_i`      | Input     | 1      | SCL line input (active state)               |
| `scl_o`      | Output    | 1      | SCL output value (always 0)                 |
| `scl_oe_o`   | Output    | 1      | SCL output enable (1 = pull low)            |
| `sda_i`      | Input     | 1      | SDA line input (active state)               |
| `sda_o`      | Output    | 1      | SDA output value (always 0)                 |
| `sda_oe_o`   | Output    | 1      | SDA output enable (1 = pull low)            |
| `intr_o`     | Output    | 16     | Interrupt vector (active-high)              |
| `alert_o`    | Output    | 1      | Fatal alert                                 |

### 3.1 Open-Drain Bus Model

The I2C bus uses open-drain signaling. The controller never drives a line high; it either releases the line (output enable deasserted, allowing an external pull-up to bring the line high) or actively pulls it low (output enable asserted). Specifically:

- `scl_o` is permanently tied to 0. `scl_oe_o` determines whether SCL is driven low.
- `sda_o` is permanently tied to 0. `sda_oe_o` determines whether SDA is driven low.
- `scl_i` and `sda_i` reflect the actual state of the bus, including contributions from other devices.

The TL-UL interface follows the same protocol as other peripherals in this design suite. A-channel transactions with `a_opcode` of `PutFullData` (0) perform writes; `Get` (4) performs reads. The device responds in the same cycle a request is accepted.

---

## 4. Register Map

Base offset: 0x00. All registers are 32 bits wide. Undefined fields read as zero; writes to undefined fields are ignored.

| Offset | Name              | Access | Description                                            |
|--------|-------------------|--------|--------------------------------------------------------|
| 0x00   | CTRL              | RW     | Controller enable and mode selection                   |
| 0x04   | STATUS            | RO     | FIFO and bus status                                    |
| 0x08   | RDATA             | RO     | Host-mode RX FIFO read port                            |
| 0x0C   | FDATA             | WO     | Format FIFO write port (host commands)                 |
| 0x10   | FIFO_CTRL         | WO     | FIFO reset controls                                    |
| 0x14   | FIFO_STATUS       | RO     | FIFO level indicators                                  |
| 0x18   | OVRD              | RW     | Bus line override for debug                            |
| 0x1C   | TIMING0           | RW     | SCL high/low period                                    |
| 0x20   | TIMING1           | RW     | Rise and fall time                                     |
| 0x24   | TIMING2           | RW     | START condition setup/hold                             |
| 0x28   | TIMING3           | RW     | Data setup/hold                                        |
| 0x2C   | TIMING4           | RW     | STOP setup and bus free time                           |
| 0x30   | TARGET_ID         | RW     | Target address and mask                                |
| 0x34   | ACQDATA           | RO     | Target-mode acquired data read port                    |
| 0x38   | TXDATA            | WO     | Target-mode transmit data write port                   |
| 0x3C   | HOST_TIMEOUT_CTRL | RW     | Host timeout configuration                             |
| 0x40   | INTR_STATE        | W1C    | Interrupt status                                       |
| 0x44   | INTR_ENABLE       | RW     | Interrupt enable mask                                  |
| 0x48   | INTR_TEST         | RW     | Interrupt test injection                               |

### 4.1 CTRL (0x00) [RW]

| Bits  | Field          | Reset | Description                                                   |
|-------|----------------|-------|---------------------------------------------------------------|
| 0     | host_enable    | 0     | Enable host (master) mode operation                           |
| 1     | target_enable  | 0     | Enable target (slave) mode operation                          |
| 2     | line_loopback  | 0     | Route SCL/SDA outputs back to inputs internally               |
| 31:3  | --             | --    | Reserved                                                      |

Enabling both host and target simultaneously is permitted but the resulting behavior depends on bus conditions and is subject to arbitration.

### 4.2 STATUS (0x04) [RO]

| Bits  | Field            | Description                                              |
|-------|------------------|----------------------------------------------------------|
| 0     | fmtfull          | Format FIFO is full                                      |
| 1     | fmtempty         | Format FIFO is empty                                     |
| 2     | txfull           | TX FIFO is full (target mode)                            |
| 3     | txempty          | TX FIFO is empty (target mode)                           |
| 4     | rxfull           | RX FIFO is full (host mode)                              |
| 5     | rxempty          | RX FIFO is empty (host mode)                             |
| 6     | host_idle        | Host FSM is idle                                         |
| 7     | target_idle      | Target FSM is idle                                       |
| 8     | bus_active       | Bus activity detected (SCL or SDA transition observed)   |
| 9     | ack_ctrl_stretch | Target is stretching the clock for ACK control           |
| 31:10 | --               | Reserved                                                 |

### 4.3 RDATA (0x08) [RO]

| Bits | Field | Description                                  |
|------|-------|----------------------------------------------|
| 7:0  | data  | Byte read from host-mode RX FIFO             |
| 31:8 | --    | Reserved                                     |

Reading RDATA when the RX FIFO is empty returns unspecified data. Each read pops one entry.

### 4.4 FDATA (0x0C) [WO]

| Bits  | Field  | Description                                             |
|-------|--------|---------------------------------------------------------|
| 7:0   | fbyte  | Data byte for write, or byte count for read operations  |
| 8     | start  | Issue START (or repeated START) before this byte        |
| 9     | stop   | Issue STOP after this byte                              |
| 10    | readb  | Byte is a read operation (fbyte = number of bytes)      |
| 11    | rcont  | Continue reading (send ACK after each byte)             |
| 12    | nakok  | Proceed even if NACK received from target               |
| 31:13 | --     | Reserved                                                |

The format FIFO encodes host-mode I2C transactions as a sequence of command entries. Each entry describes one operation on the bus. Example sequences:

- **Write one byte to target 0x50**: Two entries. First: `{start=1, fbyte=0xA0}` (START + address byte with W bit). Second: `{fbyte=data_byte, stop=1}` (data + STOP).
- **Read two bytes from target 0x50**: Three entries. First: `{start=1, fbyte=0xA1}` (START + address byte with R bit). Second: `{readb=1, rcont=1, fbyte=1}` (read 1 byte, ACK). Third: `{readb=1, fbyte=1, stop=1}` (read 1 byte, NACK, STOP).

Not all flag combinations are valid. The behavior of conflicting combinations (e.g., simultaneously asserting `start` and `stop` without data, or `readb` with non-zero `start`) follows the implementation.

### 4.5 FIFO_CTRL (0x10) [WO]

| Bits | Field    | Description                                  |
|------|----------|----------------------------------------------|
| 0    | fmt_rst  | Write 1 to flush format FIFO (self-clearing) |
| 1    | rx_rst   | Write 1 to flush RX FIFO (self-clearing)     |
| 2    | tx_rst   | Write 1 to flush TX FIFO (self-clearing)     |
| 3    | acq_rst  | Write 1 to flush acquire FIFO (self-clearing)|
| 31:4 | --       | Reserved                                     |

### 4.6 FIFO_STATUS (0x14) [RO]

| Bits   | Field   | Description                        |
|--------|---------|------------------------------------|
| 6:0    | fmtlvl  | Number of entries in format FIFO   |
| 13:7   | rxlvl   | Number of entries in RX FIFO       |
| 20:14  | txlvl   | Number of entries in TX FIFO       |
| 27:21  | acqlvl  | Number of entries in acquire FIFO  |
| 31:28  | --      | Reserved                           |

### 4.7 OVRD (0x18) [RW]

| Bits | Field    | Reset | Description                                   |
|------|----------|-------|-----------------------------------------------|
| 0    | txovrden | 0     | Enable bus line override                       |
| 1    | sclval   | 1     | SCL value when override is enabled             |
| 2    | sdaval   | 1     | SDA value when override is enabled             |
| 31:3 | --       | --    | Reserved                                       |

When `txovrden` is asserted, the SCL and SDA outputs are driven by the `sclval` and `sdaval` register fields instead of the FSMs. This mode is intended for low-level bus debugging.

### 4.8 TIMING0 through TIMING4

These registers configure the I2C bus timing in units of system clock cycles. All timing fields are 16 bits wide.

**TIMING0 (0x1C)**: `tlow[15:0]` (bits 15:0) -- SCL low period. `thigh[15:0]` (bits 31:16) -- SCL high period.

**TIMING1 (0x20)**: `t_f[15:0]` (bits 15:0) -- fall time. `t_r[15:0]` (bits 31:16) -- rise time.

**TIMING2 (0x24)**: `thd_sta[15:0]` (bits 15:0) -- hold time for START. `tsu_sta[15:0]` (bits 31:16) -- setup time for repeated START.

**TIMING3 (0x28)**: `thd_dat[15:0]` (bits 15:0) -- data hold time. `tsu_dat[15:0]` (bits 31:16) -- data setup time.

**TIMING4 (0x2C)**: `t_buf[15:0]` (bits 15:0) -- bus free time between STOP and START. `tsu_sto[15:0]` (bits 31:16) -- setup time for STOP.

Software must program these registers with values appropriate for the target bus speed and the system clock frequency. The I2C specification defines minimum values for each parameter at each speed grade.

### 4.9 TARGET_ID (0x30) [RW]

| Bits  | Field   | Reset | Description                                        |
|-------|---------|-------|----------------------------------------------------|
| 6:0   | address | 0     | 7-bit I2C target address                           |
| 13:7  | mask    | 0     | Address mask (1 = must match, 0 = don't care)      |
| 31:14 | --      | --    | Reserved                                           |

In target mode, incoming address bytes are compared against `address` using `mask`. For each bit position where the corresponding mask bit is 1, the received address bit must match the configured address bit. Mask bits set to 0 act as wildcards.

### 4.10 ACQDATA (0x34) [RO]

| Bits  | Field  | Description                                          |
|-------|--------|------------------------------------------------------|
| 7:0   | data   | Acquired data byte (target mode)                     |
| 9:8   | signal | Signal type indicator                                |
| 31:10 | --     | Reserved                                             |

The acquire FIFO stores data received by the target FSM from a host on the bus. The `signal` field encodes additional protocol information associated with the data byte. The encoding of signal values follows standard I2C controller conventions.

### 4.11 TXDATA (0x38) [WO]

| Bits | Field | Description                           |
|------|-------|---------------------------------------|
| 7:0  | data  | Data byte to transmit in target mode  |
| 31:8 | --    | Reserved                              |

### 4.12 HOST_TIMEOUT_CTRL (0x3C) [RW]

| Bits  | Field       | Reset | Description                                      |
|-------|-------------|-------|--------------------------------------------------|
| 19:0  | timeout_val | 0     | Timeout threshold in clock cycles                |
| 20    | timeout_en  | 0     | Enable host timeout detection                    |
| 31:21 | --          | --    | Reserved                                         |

When enabled, the controller monitors SCL for prolonged low periods. If SCL remains low for more than `timeout_val` clock cycles, a host timeout interrupt is raised. This detects situations where a target device holds the clock low indefinitely.

### 4.13 Interrupt Registers

**INTR_STATE (0x40)** [W1C]: Current interrupt status. Writing 1 clears the corresponding bit.

**INTR_ENABLE (0x44)** [RW]: Per-source interrupt enable mask.

**INTR_TEST (0x48)** [RW]: Writing 1 to any bit forces the corresponding INTR_STATE bit to set.

The interrupt output vector `intr_o[15:0]` is computed as `intr_state & intr_enable`.

| Bit | Source            | Description                                           |
|-----|-------------------|-------------------------------------------------------|
| 0   | fmt_threshold     | Format FIFO level below threshold                     |
| 1   | rx_threshold      | RX FIFO level above threshold                         |
| 2   | fmt_overflow      | Write to format FIFO when full                        |
| 3   | rx_overflow       | RX FIFO overflow                                      |
| 4   | nak               | NACK received in host mode                            |
| 5   | scl_interference  | SCL line driven low when controller expected high     |
| 6   | sda_interference  | SDA line unexpected transition                        |
| 7   | stretch_timeout   | Target clock stretching exceeded timeout              |
| 8   | sda_unstable      | SDA changed while SCL was high (outside START/STOP)   |
| 9   | trans_complete    | Host-mode transaction completed (format FIFO drained) |
| 10  | tx_empty          | TX FIFO empty (target mode)                           |
| 11  | tx_nonempty       | TX FIFO has data (target mode)                        |
| 12  | tx_overflow       | TX FIFO overflow (target mode)                        |
| 13  | acq_full          | Acquire FIFO full (target mode)                       |
| 14  | ack_stop          | Target received STOP or repeated START after ACK      |
| 15  | host_timeout      | SCL held low longer than timeout value                |

---

## 5. Host Mode Operation

### 5.1 Format FIFO Command Processing

When host mode is enabled, the host FSM reads entries from the format FIFO and executes them sequentially on the I2C bus. Each entry may trigger a START condition, transmit or receive one or more bytes, and optionally terminate with a STOP condition. The FSM idles when the format FIFO is empty.

The host FSM generates SCL according to the programmed timing parameters. During write operations, it places bits on SDA synchronized to SCL transitions. During read operations, it releases SDA and samples incoming data at the appropriate point in the SCL cycle.

### 5.2 Byte Transmission

For each byte transmitted (address or data), the host clocks out 8 bits MSB-first on SDA. After the 8th bit, the host releases SDA for one clock period and samples the ACK/NACK response from the target. If NACK is received and the NAKOK flag is not set on the current format entry, the host FSM raises the `nak` interrupt and halts. If NAKOK is set, the FSM proceeds to the next format entry.

### 5.3 Byte Reception

When a format entry has the `readb` flag set, the host releases SDA and clocks in data bytes. The `fbyte` field specifies how many bytes to read. After each byte, the host sends an ACK if `rcont` is set, or a NACK if `rcont` is not set (indicating the last byte of the read sequence). Received bytes are placed in the RX FIFO.

### 5.4 Bus Conditions

**START**: SDA transitions from high to low while SCL is high. The timing of this transition relative to SCL is governed by the `tsu_sta` and `thd_sta` parameters.

**Repeated START**: A START condition issued without an intervening STOP. The host must first bring SDA high, then follow the standard START timing.

**STOP**: SDA transitions from low to high while SCL is high. The `tsu_sto` parameter governs the setup time.

### 5.5 Arbitration

In multi-master configurations, the host monitors SDA during transmission. If the host drives SDA high but reads SDA low (another master is pulling it down), an arbitration loss is detected. Upon arbitration loss, the host ceases driving the bus per the I2C specification. The details of bus recovery following arbitration loss are implementation-specific and follow standard I2C multi-master conventions.

---

## 6. Target Mode Operation

### 6.1 Address Recognition

When target mode is enabled, the target FSM monitors the bus for START conditions. Upon detecting a START, it shifts in the subsequent 7 address bits and R/W direction bit. The received address is compared against TARGET_ID using the configured mask. If the address matches, the target sends an ACK and proceeds with the transaction. If it does not match, the target ignores the remainder of the transaction.

### 6.2 Data Reception (Host Write to Target)

When the direction bit indicates a write, the target receives data bytes from the host. Each received byte is stored in the acquire FIFO and acknowledged. The behavior when the acquire FIFO is full during reception is governed by the I2C specification's conventions for flow control.

### 6.3 Data Transmission (Host Read from Target)

When the direction bit indicates a read, the target transmits data from the TX FIFO to the host. The target places bits on SDA and the host clocks them out via SCL. After each byte, the host sends ACK to continue or NACK to end the transfer.

### 6.4 Clock Stretching

The target may stretch the clock (hold SCL low) when it needs time to prepare data. Clock stretching occurs primarily when the TX FIFO is empty during a read operation or when the acquire FIFO requires software attention. The target releases SCL when the condition is resolved. The exact release timing relative to FIFO state changes is not specified beyond standard I2C compliance.

---

## 7. Bus Override

When OVRD.txovrden is set, the SCL and SDA output enables are controlled directly by the OVRD register values rather than the FSMs. This is intended for manufacturing test and low-level debug. Bus override should only be used when both host and target modes are disabled; behavior when override is active during normal operation is undefined.

---

## 8. Line Loopback

When CTRL.line_loopback is set, the controller's SCL and SDA outputs are internally routed back to the corresponding inputs, bypassing the external bus. This mode enables self-test without external I2C devices. The external `scl_i` and `sda_i` pins are ignored during loopback.

---

## 9. Reset Behavior

On assertion of `rst_ni` (active-low), all registers return to their reset values, all FIFOs are flushed, both FSMs return to idle, and the bus lines are released (output enables deasserted). The reset is asynchronous.

---

## 10. Alert Output

The `alert_o` signal is reserved for fatal hardware errors such as FIFO integrity failures or unrecoverable state machine errors. Under normal operation it remains deasserted.
