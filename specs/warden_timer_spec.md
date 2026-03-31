# WARDEN_TIMER -- Timer/Watchdog Module Specification

> **Disclaimer:** This RTL design is a modified version of an open-source IP block, created exclusively for this competition. It is not production-quality, not security-reviewed, and must not be used outside of this competition context.

---

## 1. Overview

WARDEN_TIMER is a combined timer and watchdog peripheral intended for RISC-V-class systems. It provides:

- A 64-bit free-running monotonic counter (`mtime`) with a configurable 12-bit prescaler.
- Two independent 64-bit timer comparators (`mtimecmp0`, `mtimecmp1`) that generate interrupts when the counter reaches or exceeds their programmed values.
- A watchdog timer with configurable bark (warning) and bite (fatal) thresholds, requiring periodic software "pet" writes to prevent timeout escalation.

The module exposes a register-mapped CSR interface over a simplified TileLink-UL (TL-UL) bus. All registers are 32 bits wide; 64-bit values are accessed as paired LOW/HIGH registers.

---

## 2. Functional Description

### 2.1 Main Timer (mtime)

The main timer is a 64-bit free-running counter that increments monotonically from its reset value of zero. The rate of increment is governed by the prescaler register: `mtime` advances by one for every `(PRESCALER + 1)` clock cycles. When the prescaler is 0, `mtime` increments on every clock cycle.

An internal prescale counter counts from 0 up to the programmed prescaler value. When the prescale counter reaches the prescaler value, it wraps back to 0 and `mtime` is incremented. The prescale counter is not directly visible to software.

If the prescaler value is changed while counting is active, the new prescaler value takes effect on the next prescaler cycle boundary. The prescale counter is not explicitly reset on a prescaler register write.

The `mtime` counter cannot be written by software; it is strictly read-only. On reset, `mtime` is initialized to zero.

### 2.2 Timer Comparators

Two independent comparators continuously compare the current `mtime` value against their respective 64-bit thresholds (`mtimecmp0` and `mtimecmp1`). Each comparator uses an unsigned greater-than-or-equal comparison:

- When `mtime >= mtimecmp0`, the `timer0_expired` interrupt condition is raised.
- When `mtime >= mtimecmp1`, the `timer1_expired` interrupt condition is raised.

Once an interrupt condition is raised, it remains asserted until software clears it by writing a 1 to the corresponding bit in `INTR_STATE`. Software may also suppress the interrupt output by clearing the corresponding bit in `INTR_ENABLE`.

The comparator values are written as two separate 32-bit register writes (LOW half, then HIGH half, or vice versa). Software should consider the intermediate state where only one half has been updated. The module does not provide any atomic 64-bit write mechanism for the comparator registers.

### 2.3 Watchdog Timer

The watchdog timer is an independent 32-bit counter that increments on every clock cycle when enabled. It provides two escalation thresholds:

- **Bark threshold** (`WATCHDOG_BARK_THRESH`): When the watchdog counter reaches this value, the `watchdog_bark` interrupt is raised as a warning to software.
- **Bite threshold** (`WATCHDOG_BITE_THRESH`): When the watchdog counter reaches this value, the `alert_o` signal is asserted, indicating a fatal condition. The bite alert is intended to trigger a system-level reset or similar recovery action.

The watchdog counter is reset to zero by writing any value to the `WATCHDOG_PET` register. Software is expected to periodically pet the watchdog before the bark threshold is reached.

The watchdog is enabled and controlled via the `WATCHDOG_CTRL` register. The watchdog counter only increments when `wd_enable` is set.

### 2.4 Watchdog Lock

The `WATCHDOG_CTRL` register contains a `wd_lock` bit. Once this bit is set by software, it cannot be cleared except by a full hardware reset (`rst_ni` assertion). When the watchdog is in locked mode, the configuration is frozen to prevent software from inadvertently or maliciously disabling the watchdog.

In locked mode, writes to `WATCHDOG_CTRL` are restricted. The `WATCHDOG_PET` register remains writable at all times regardless of lock state, so that software may continue to service the watchdog.

### 2.5 Interrupts and Alert

The module provides three interrupt sources and one alert output:

| Signal         | Type      | Description                                         |
|----------------|-----------|-----------------------------------------------------|
| `intr_o[0]`    | Interrupt | `timer0_expired` -- mtime >= mtimecmp0              |
| `intr_o[1]`    | Interrupt | `timer1_expired` -- mtime >= mtimecmp1              |
| `intr_o[2]`    | Interrupt | `watchdog_bark` -- watchdog counter >= bark thresh   |
| `alert_o`      | Alert     | `watchdog_bite` -- watchdog counter >= bite thresh   |

Interrupts follow the standard interrupt CSR triplet pattern:

- **INTR_STATE** (W1C): Shows current raw interrupt status. Writing a 1 to a bit clears that interrupt.
- **INTR_ENABLE**: Masks interrupt output. The output pin `intr_o[n]` is asserted only when both `INTR_STATE[n]` and `INTR_ENABLE[n]` are set.
- **INTR_TEST**: Writing a 1 to any bit sets the corresponding bit in `INTR_STATE`, allowing software to test interrupt handling without waiting for actual hardware events.

The `alert_o` output is asserted directly when the watchdog counter reaches the bite threshold. It is not maskable and is not part of the interrupt state register.

---

## 3. Register Map

All registers are 32 bits wide, aligned to 4-byte boundaries. The module occupies a 64-byte address window.

| Offset | Name                  | Access | Reset Value | Description                                        |
|--------|-----------------------|--------|-------------|----------------------------------------------------|
| 0x00   | MTIME_LOW             | RO     | 0x0         | Lower 32 bits of the 64-bit mtime counter          |
| 0x04   | MTIME_HIGH            | RO     | 0x0         | Upper 32 bits of the 64-bit mtime counter          |
| 0x08   | MTIMECMP0_LOW         | RW     | 0x0         | Lower 32 bits of timer comparator 0                |
| 0x0C   | MTIMECMP0_HIGH        | RW     | 0x0         | Upper 32 bits of timer comparator 0                |
| 0x10   | MTIMECMP1_LOW         | RW     | 0x0         | Lower 32 bits of timer comparator 1                |
| 0x14   | MTIMECMP1_HIGH        | RW     | 0x0         | Upper 32 bits of timer comparator 1                |
| 0x18   | PRESCALER             | RW     | 0x0         | Prescaler value (bits [11:0] only; upper bits RAZ) |
| 0x1C   | WATCHDOG_CTRL         | RW     | 0x0         | Watchdog control: bit 0 = wd_enable, bit 1 = wd_lock |
| 0x20   | WATCHDOG_BARK_THRESH  | RW     | 0x0         | 32-bit bark (warning) threshold                    |
| 0x24   | WATCHDOG_BITE_THRESH  | RW     | 0x0         | 32-bit bite (fatal) threshold                      |
| 0x28   | WATCHDOG_PET          | WO     | --          | Write any value to reset watchdog counter to 0      |
| 0x2C   | WATCHDOG_COUNT        | RO     | 0x0         | Current watchdog counter value                     |
| 0x30   | INTR_STATE            | W1C    | 0x0         | Interrupt status (bits [2:0])                      |
| 0x34   | INTR_ENABLE           | RW     | 0x0         | Interrupt enable mask (bits [2:0])                 |
| 0x38   | INTR_TEST             | RW     | 0x0         | Interrupt test register (bits [2:0])               |

### 3.1 Register Field Details

**PRESCALER (0x18)**
- Bits [11:0]: Prescaler value. The main timer increments once every (prescaler + 1) clock cycles.
- Bits [31:12]: Reserved, read as zero.

**WATCHDOG_CTRL (0x1C)**
- Bit 0: `wd_enable` -- enables the watchdog counter.
- Bit 1: `wd_lock` -- once set, cannot be cleared except by hardware reset.
- Bits [31:2]: Reserved, read as zero.

**WATCHDOG_PET (0x28)**
- Write-only. Any write resets the internal watchdog counter to zero.
- Reads from this address return 0.

**INTR_STATE (0x30)**
- Bit 0: `timer0_expired`
- Bit 1: `timer1_expired`
- Bit 2: `watchdog_bark`
- Write-1-to-clear: writing a 1 to a bit clears that interrupt status bit.

---

## 4. Bus Interface

The module uses a simplified TileLink-UL interface as defined in `dv_common_pkg`. The interface supports single 32-bit read and write transactions.

- **Channel A** (host to device): Carries read (`Get`, opcode 4) and write (`PutFullData`, opcode 0) requests.
- **Channel D** (device to host): Returns read data (`AccessAckData`, opcode 1) or write acknowledgments (`AccessAck`, opcode 0).

The module is expected to respond to every valid Channel A request within a single cycle (no wait states). Transactions to addresses outside the defined register map should complete normally but return zero for reads and ignore data for writes.

Flow control uses a ready/valid handshake: a transaction occurs when both `valid` and `ready` are asserted on the same clock edge.

---

## 5. Reset Behavior

On assertion of the active-low asynchronous reset (`rst_ni`):

- `mtime` is cleared to zero.
- Both comparators (`mtimecmp0`, `mtimecmp1`) are cleared to zero.
- The prescaler is cleared to zero (mtime increments every clock cycle after reset).
- The watchdog is disabled (`wd_enable` = 0, `wd_lock` = 0).
- The watchdog counter is cleared to zero.
- Bark and bite thresholds are cleared to zero.
- All interrupt state, enable, and test registers are cleared.
- The `alert_o` output is deasserted.

---

## 6. Timing Considerations

- The prescaler affects only the main `mtime` counter. The watchdog counter always increments at the system clock rate when enabled.
- Software reading `MTIME_LOW` followed by `MTIME_HIGH` should be aware that the counter may increment between the two reads. The module does not implement any read-coherency mechanism for the 64-bit mtime value.
- Interrupt outputs reflect the combined state of `INTR_STATE` and `INTR_ENABLE` combinationally. Changes to either register are visible on `intr_o` in the same cycle.
- The watchdog bite alert is combinational with respect to the threshold comparison.
