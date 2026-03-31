# Task 1.1: Interface Agent Generation

**Phase 1 | 300 points per DUT | Up to 3 DUTs | Max 900 points**

---

## Overview

Design and implement complete UVM verification agents for the DUTs provided in the Agentic AI Design Verification Challenge 2026. Each submission must include a reusable TileLink-UL bus agent, protocol-specific agents where applicable, a scoreboard with a behavioral reference model, and a top-level verification environment that ties everything together.

This task evaluates your ability to produce structurally sound, functionally correct verification IP from DUT specifications and RTL alone.

---

## Available DUTs

| Tier | DUT Name | Protocol | Approx. Lines | Protocol Agent Required? |
|------|----------|----------|---------------|--------------------------|
| Tier 1 (Starter) | `nexus_uart` | UART | ~500 | Yes |
| Tier 1 (Starter) | `bastion_gpio` | GPIO | ~400 | Yes (stimulus driver) |
| Tier 2 (Intermediate) | `warden_timer` | Timer/Watchdog | ~600 | No (CSR-only) |
| Tier 2 (Intermediate) | `citadel_spi` | SPI Host | ~900 | Yes |
| Tier 3 (Advanced) | `aegis_aes` | AES-128 | ~1200 | No (CSR-only) |
| Tier 3 (Advanced) | `sentinel_hmac` | HMAC-SHA256 | ~1000 | No (CSR-only) |
| Tier 4 (Expert) | `rampart_i2c` | I2C Host/Target | ~1100 | Yes |

All DUTs share a common **TileLink-UL simplified bus interface** (`tl_i`/`tl_o` with ready/valid handshake), active-low asynchronous reset (`rst_ni`), and standard interrupt (`intr_o`) and alert (`alert_o`) outputs.

You may submit agents for **up to 3 DUTs**. Choose strategically based on your strengths and the points-per-effort trade-off.

---

## What to Build

### 1. TL-UL Bus Agent (Reusable)

A single, parameterized UVM agent for the TileLink-UL bus interface. This agent must be reusable across all DUTs without modification.

**Required components:**

- **Driver** (`tl_ul_driver`): Drives `tl_i` (a_valid, a_opcode, a_addr, a_data, a_mask, d_ready) according to TL-UL protocol rules.
- **Monitor** (`tl_ul_monitor`): Observes both `tl_i` and `tl_o` channels, capturing completed transactions on the analysis port.
- **Sequencer** (`tl_ul_sequencer`): Standard UVM sequencer for `tl_ul_seq_item`.
- **Sequences**: At minimum, provide:
  - `tl_ul_write_seq` -- single CSR write
  - `tl_ul_read_seq` -- single CSR read
  - `tl_ul_burst_seq` -- back-to-back transactions
  - `tl_ul_random_seq` -- randomized address/data/delay

**Transaction item fields:**

```systemverilog
class tl_ul_seq_item extends uvm_sequence_item;
  rand bit [31:0] addr;
  rand bit [31:0] data;
  rand bit [3:0]  mask;
  rand tl_opcode_e opcode;  // PutFullData, PutPartialData, Get
  rand int unsigned delay;

  bit [31:0] rdata;         // Response data (filled by driver/monitor)
  bit        error;         // Response error (filled by driver/monitor)
  // ...
endclass
```

### 2. Protocol-Specific Agent (per DUT, where applicable)

Build a protocol-side agent that models the external interface of the DUT. Not all DUTs require one.

| DUT | Agent Type | Key Requirements |
|-----|-----------|------------------|
| `nexus_uart` | UART Agent | Configurable baud rate, parity modes, start/stop bit handling |
| `bastion_gpio` | GPIO Stimulus Driver | Drive/sample individual pins, support interrupt-on-change |
| `citadel_spi` | SPI Agent | All 4 SPI modes (CPOL/CPHA), configurable clock divider, CS handling |
| `rampart_i2c` | I2C Agent | Open-drain modeling, clock stretching, arbitration, ACK/NACK |
| `warden_timer` | _None_ | CSR-only; no external protocol interface |
| `aegis_aes` | _None_ | CSR-only; data loaded via TL-UL registers |
| `sentinel_hmac` | _None_ | CSR-only; data loaded via TL-UL registers |

Each protocol agent must include a driver, monitor, and at least two directed sequences.

### 3. Scoreboard

Each DUT submission must include a scoreboard containing:

- **Behavioral reference model** written in Python (executed via DPI-C or cocotb bridge, or as a standalone checker script). The model must accept the same stimulus as the DUT and produce expected outputs.
- **Comparison logic** that matches DUT outputs against the reference model, reporting mismatches with transaction-level detail.

Example structure for `nexus_uart`:

```python
class UartRefModel:
    def __init__(self, baud_rate=115200, parity='none', data_bits=8):
        self.baud_rate = baud_rate
        self.parity = parity
        self.data_bits = data_bits
        self.tx_fifo = []
        self.rx_fifo = []

    def csr_write(self, addr, data):
        """Process a CSR write and update internal state."""
        if addr == UART_CTRL_OFFSET:
            self._configure(data)
        elif addr == UART_WDATA_OFFSET:
            self.tx_fifo.append(data & 0xFF)
            # ...

    def predict_tx(self):
        """Return expected serial output for next TX byte."""
        if not self.tx_fifo:
            return None
        byte = self.tx_fifo.pop(0)
        return self._frame_byte(byte)
```

### 4. Verification Environment

A top-level UVM environment class that instantiates and connects all components:

- TL-UL agent (active)
- Protocol-specific agent (active or passive, as appropriate)
- Scoreboard
- Coverage collectors (functional coverage groups for CSR access patterns and protocol events)

```systemverilog
class uart_env extends uvm_env;
  tl_ul_agent    m_tl_agent;
  uart_agent     m_uart_agent;
  uart_scoreboard m_scoreboard;
  uart_coverage   m_coverage;

  // build_phase: create and configure components
  // connect_phase: wire analysis ports
endclass
```

---

## Submission Format

Your submission directory for each DUT must follow this structure:

```
submission/
  task_1_1/
    <dut_name>/
      agents/
        tl_ul/              # Reusable TL-UL agent (same across DUTs)
          tl_ul_agent.sv
          tl_ul_driver.sv
          tl_ul_monitor.sv
          tl_ul_sequencer.sv
          tl_ul_seq_item.sv
          tl_ul_sequences.sv
        <protocol>/         # Protocol-specific agent (if applicable)
          <protocol>_agent.sv
          <protocol>_driver.sv
          <protocol>_monitor.sv
          <protocol>_seq_item.sv
          <protocol>_sequences.sv
      scoreboard/
        <dut>_scoreboard.sv
        ref_model/
          <dut>_ref_model.py
      env/
        <dut>_env.sv
        <dut>_coverage.sv
      tb/
        <dut>_tb_top.sv      # Top-level testbench module
      filelist.f             # Compilation file list
```

A `filelist.f` must be provided that compiles cleanly with the platform's simulator when combined with the provided RTL.

---

## Evaluation Rubric

### Automated Scoring (80% -- 240 points per DUT)

| Category | Points | Criteria |
|----------|--------|----------|
| **Compilability** | 60 pts (20%) | Submission compiles without errors when combined with reference RTL. Partial credit: compiles with warnings only (40 pts). |
| **Structural Completeness** | 90 pts (30%) | All required components present and properly connected. Checked via static analysis: agent/driver/monitor/sequencer hierarchy, scoreboard instantiation, coverage collector presence, analysis port connections. |
| **Functional Correctness** | 90 pts (30%) | A battery of platform-provided test sequences is run through the submitted environment against the clean reference RTL. Graded on: transactions complete without UVM_ERROR (30 pts), scoreboard reports zero mismatches (30 pts), coverage collectors produce non-zero coverage (30 pts). |

### Judge Scoring (20% -- 60 points per DUT)

| Category | Points | Criteria |
|----------|--------|----------|
| **Code Quality** | 20 pts | Consistent naming conventions, proper UVM macros, meaningful comments, clean structure. |
| **Best Practices** | 20 pts | Proper use of UVM phases, factory overrides, configuration database, TLM ports. Avoidance of anti-patterns (hardcoded delays, absolute time references, non-parameterized widths). |
| **Reusability** | 20 pts | TL-UL agent truly reusable without edits. Protocol agent parameterized where sensible. Environment configurable via `uvm_config_db`. |

---

## Tips for AI-Assisted Development

1. **Start with the TL-UL agent.** It is shared across all DUTs, so getting it right pays dividends. Study the TL-UL specification provided in the reference materials.

2. **Use the RTL port list as your ground truth.** Extract the DUT's I/O ports and use them to define your interface and agent structure before writing any behavioral code.

3. **Iterate on compilation.** The most common failure mode is submitting code that does not compile. Run your agent through a compile-check loop before submission.

4. **Keep the reference model simple.** A correct but minimal Python model beats an elaborate but buggy one. Focus on the core data path first, then add edge cases.

5. **Test your scoreboard independently.** Feed known-good stimulus/response pairs into your comparison logic before integrating with the full environment.

6. **Leverage the CSR map.** The Hjson register descriptions provide exact field widths, reset values, and access types -- use them to auto-generate CSR access helpers in your reference model.
