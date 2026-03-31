# BASTION_GPIO Specification

## General-Purpose I/O Controller

> **Disclaimer:** This RTL design is a modified version of an open-source IP block, created exclusively for this competition. It is not production-quality, not security-reviewed, and must not be used outside of this competition context.

---

## 1. Overview

BASTION_GPIO is a 32-pin general-purpose I/O controller. Each pin is independently configurable as either an input or an output. The module provides input synchronization for metastability hardening, per-pin edge and level-sensitive interrupt generation, and a masked write mechanism that allows atomic modification of output pins without requiring a read-modify-write sequence.

The controller connects to the system fabric via a TileLink-UL (TL-UL) bus interface and exposes a set of control/status registers (CSRs) for configuration and data access. All 32 GPIO pins share a single consolidated interrupt output vector (`intr_o[31:0]`), with one interrupt line per pin, as well as a single `alert_o` output.

---

## 2. Pin Interface

| Signal        | Width | Direction | Description                                  |
|---------------|-------|-----------|----------------------------------------------|
| `clk_i`       | 1     | Input     | System clock                                 |
| `rst_ni`      | 1     | Input     | Active-low asynchronous reset                |
| `tl_i`        | struct | Input    | TL-UL request channel (host to device)       |
| `tl_i_ready`  | 1     | Output    | Device ready to accept TL-UL request         |
| `tl_o`        | struct | Output   | TL-UL response channel (device to host)      |
| `tl_o_ready`  | 1     | Input     | Host ready to accept TL-UL response          |
| `gpio_i`      | 32    | Input     | External pin input values                    |
| `gpio_o`      | 32    | Output    | Pin output values                            |
| `gpio_oe_o`   | 32    | Output    | Per-pin output enable (1 = driving)          |
| `intr_o`      | 32    | Output    | Interrupt output, one per pin                |
| `alert_o`     | 1     | Output    | Alert output                                 |

---

## 3. Functional Description

### 3.1 Pin Direction and Output Control

Each of the 32 GPIO pins can be configured independently as an input or output via the **DIR** register. When a pin is configured as an output (`DIR[n] = 1`), the value in **DATA_OUT[n]** is driven onto `gpio_o[n]`, and `gpio_oe_o[n]` is asserted. When configured as an input (`DIR[n] = 0`), `gpio_oe_o[n]` is deasserted, and the pin's external value is captured through the input synchronizer. The behavior during a direction transition is implementation-dependent; software should avoid relying on specific ordering of the direction change relative to data path updates.

### 3.2 Input Synchronization

All 32 input pins pass through a two-stage synchronizer before being visible to the register interface. This provides metastability hardening for asynchronous external inputs. The synchronized values are available in the **DATA_IN** register.

The synchronizer introduces a two-clock-cycle latency between an external pin transition and its visibility in DATA_IN. The synchronizer also provides inherent glitch filtering for very narrow pulses, though the precise minimum pulse width that is guaranteed to be captured is a function of the synchronizer's sampling characteristics and process parameters.

### 3.3 Edge Detection

The controller compares the current synchronized input value against the value from the previous clock cycle to detect edges. A rising edge on pin N is detected when the previous value was 0 and the current value is 1. A falling edge is the converse.

Edge detection operates on the synchronized input values (after the two-stage synchronizer), not on the raw `gpio_i` inputs.

Whether simultaneous edges on multiple pins within the same clock cycle are all reliably captured depends on internal arbitration. In general, all detected edges should be reflected in the interrupt state, but under certain conditions involving very high pin activity the controller may exhibit priority behavior.

### 3.4 Interrupt Generation

Each pin supports four independent interrupt trigger modes, controlled by separate enable registers:

- **Rising edge** (`INTR_CTRL_EN_RISING`): Interrupt fires on a detected rising edge
- **Falling edge** (`INTR_CTRL_EN_FALLING`): Interrupt fires on a detected falling edge
- **Level high** (`INTR_CTRL_EN_LVLHIGH`): Interrupt is asserted continuously while the synchronized input is high
- **Level low** (`INTR_CTRL_EN_LVLLOW`): Interrupt is asserted continuously while the synchronized input is low

Multiple modes may be enabled simultaneously for the same pin. When a level-sensitive interrupt is cleared via a W1C write to INTR_STATE while the triggering condition still holds, the interrupt should re-assert. Edge-triggered interrupts are latched in INTR_STATE upon detection and remain set until cleared by software.

The per-pin interrupt output `intr_o[n]` reflects `INTR_STATE[n] & INTR_ENABLE[n]`.

### 3.5 Masked Writes

The masked write registers allow software to atomically set or clear specific output pins without performing a read-modify-write on DATA_OUT. This is critical for safe concurrent access to GPIO pins from multiple software contexts.

**MASKED_OUT_LOWER** controls pins [15:0]. The upper 16 bits of the write data serve as a mask: for each bit position `k` in [15:0], if `write_data[k+16]` is 1, then `DATA_OUT[k]` is updated with `write_data[k]`. Bits where the mask is 0 are left unchanged.

**MASKED_OUT_UPPER** controls pins [31:16]. The upper 16 bits of the write data serve as a mask: for each bit position `k` in [15:0], if `write_data[k+16]` is 1, then `DATA_OUT[k+16]` is updated with `write_data[k]`. Bits where the mask is 0 are left unchanged.

Reading MASKED_OUT_LOWER returns the current value of DATA_OUT[15:0] in the lower 16 bits; the upper 16 bits read as zero. Reading MASKED_OUT_UPPER returns the current value of DATA_OUT[31:16] in the lower 16 bits; the upper 16 bits read as zero.

The interaction between a masked write and a simultaneous direct write to DIR or DATA_OUT in the same bus cycle is not fully specified. Software should ensure that masked writes and direct CSR writes to related registers do not collide.

### 3.6 Interrupt Test

The **INTR_TEST** register allows software to inject interrupt events for diagnostic purposes. Writing a 1 to bit N of INTR_TEST causes `INTR_STATE[N]` to be set, as if the corresponding interrupt event had occurred. This is useful for testing interrupt handler software without requiring external stimulus.

---

## 4. CSR Register Map

All registers are 32 bits wide. Byte address offsets are given relative to the module base address.

| Offset | Name                    | Access | Description                                              |
|--------|-------------------------|--------|----------------------------------------------------------|
| 0x00   | DATA_IN                 | RO     | Synchronized input pin values                            |
| 0x04   | DATA_OUT                | RW     | Output pin values                                        |
| 0x08   | DIR                     | RW     | Pin direction (0 = input, 1 = output)                    |
| 0x0C   | INTR_STATE              | W1C    | Interrupt status (write 1 to clear)                      |
| 0x10   | INTR_ENABLE             | RW     | Per-pin interrupt enable                                 |
| 0x14   | INTR_TEST               | RW     | Interrupt test (write 1 to set INTR_STATE)               |
| 0x18   | INTR_CTRL_EN_RISING     | RW     | Enable rising-edge interrupt per pin                     |
| 0x1C   | INTR_CTRL_EN_FALLING    | RW     | Enable falling-edge interrupt per pin                    |
| 0x20   | INTR_CTRL_EN_LVLHIGH   | RW     | Enable level-high interrupt per pin                      |
| 0x24   | INTR_CTRL_EN_LVLLOW    | RW     | Enable level-low interrupt per pin                       |
| 0x28   | MASKED_OUT_LOWER        | RW     | Masked write for pins [15:0]; read returns DATA_OUT[15:0]|
| 0x2C   | MASKED_OUT_UPPER        | RW     | Masked write for pins [31:16]; read returns DATA_OUT[31:16]|

### Register Reset Values

All RW registers reset to 0x00000000. DATA_IN reflects the synchronized state of the external pins after reset (which depends on external conditions). INTR_STATE resets to 0.

### CSR Access Notes

- Writes to DATA_IN (read-only) are silently ignored and generate no bus error.
- INTR_STATE uses W1C semantics: writing a 1 to a bit clears that bit; writing a 0 has no effect.
- INTR_TEST writes are edge-sensitive in the sense that writing a 1 sets the corresponding INTR_STATE bit, but does not hold it. The INTR_STATE bit then follows normal W1C clearing behavior.
- Unimplemented or reserved address ranges return 0 on read and ignore writes.

---

## 5. Timing Considerations

- Input synchronizer latency: 2 clock cycles from `gpio_i` change to `DATA_IN` update.
- Edge detection occurs on the cycle following the synchronized value change.
- Interrupt output (`intr_o`) updates combinationally from INTR_STATE and INTR_ENABLE. There is no additional pipeline delay on the interrupt path.
- Masked writes take effect in the same cycle as a normal DATA_OUT write.
- The TL-UL interface responds in a single cycle for all CSR accesses (no wait states).

---

## 6. Alert Behavior

The `alert_o` signal is reserved for fatal error conditions. Under normal operation, `alert_o` remains deasserted. The conditions under which an alert may be raised are related to internal consistency checks and are not enumerated in detail here.
