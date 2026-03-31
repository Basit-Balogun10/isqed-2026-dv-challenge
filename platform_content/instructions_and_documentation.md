# Instructions & Documentation

## Agentic AI Design Verification Challenge 2026 -- ISQED 2026

This document provides everything you need to participate in the Agentic AI Design Verification Challenge. Read it carefully before beginning work on any task.

---

## 1. Getting Started

### Accessing Competition Materials

All competition materials are available for download directly from the platform. After registering and joining a task, download the materials package from the task dashboard. The package contains RTL source files, specifications, starter environments, and verification plan templates for every DUT in the competition.

### Project Directory Structure

Once downloaded and extracted, the materials are organized as follows:

```
competition-materials/
├── duts/              — RTL source for all DUTs (SystemVerilog)
│   ├── common/        — Shared packages, TL-UL interface definitions
│   ├── nexus_uart/    — UART controller
│   ├── bastion_gpio/  — GPIO controller
│   ├── warden_timer/  — Timer/watchdog
│   ├── citadel_spi/   — SPI host controller
│   ├── aegis_aes/     — AES-128 engine
│   ├── sentinel_hmac/ — HMAC-SHA256 accelerator
│   └── rampart_i2c/   — I2C host/target controller
├── specs/             — Specification documents per DUT (markdown)
├── csr_maps/          — Register maps in Hjson format
├── skeleton_envs/     — Starter cocotb environments
├── reference_tb/      — Baseline testbenches (~40% coverage)
└── vplans/            — Verification plan templates (YAML)
```

Each DUT directory under `duts/` contains the complete SystemVerilog source needed for simulation. The `common/` directory holds shared packages and the TL-UL interface definitions used by every DUT.

---

## 2. Toolchain Setup

The competition supports two verification paths. Choose the one that best fits your team's expertise and available tools.

### Path A — Python-Based Verification (Open-Source)

This is the **recommended starting point** for most teams. All skeleton environments and reference testbenches are provided in this format. No commercial licenses required.

**Required tools:**

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Verilator | 5.x | Primary simulator and coverage collection |
| Icarus Verilog | 12+ | Secondary simulator |
| cocotb | 1.9+ | Python-based testbench framework |
| pyuvm | 3.0+ | UVM methodology in Python (agents, sequences, factory, config_db) |
| cocotb-coverage | latest | Functional coverage (coverpoints, crosses, bins) |
| Python | 3.11+ | Runtime |

**Python packages:**

```bash
pip install cocotb cocotb-bus cocotb-coverage pyuvm \
    numpy scipy pandas pyyaml jinja2 hjson
```

**Quick start (Path A):**

```bash
# Compile with Verilator
verilator --cc --exe --build \
    duts/common/dv_common_pkg.sv \
    duts/nexus_uart/nexus_uart.sv

# Compile with Icarus Verilog
iverilog -g2012 -o sim \
    duts/common/dv_common_pkg.sv \
    duts/nexus_uart/nexus_uart.sv

# Run a reference testbench with cocotb
cd skeleton_envs/nexus_uart
make SIM=icarus
```

If all three commands complete without errors, your Path A environment is ready.

### Path B — SystemVerilog UVM (Commercial Simulators)

Teams with access to commercial EDA tool licenses may build full SystemVerilog UVM testbenches. This path enables native constrained-random stimulus, the full UVM class library, SystemVerilog Assertions (SVA), and SystemVerilog functional coverage.

**Supported simulators:**

| Simulator | Vendor | Minimum Version |
|-----------|--------|-----------------|
| VCS | Synopsys | 2023.x or later |
| Questa / QuestaSim | Siemens EDA | 2023.x or later |
| Xcelium | Cadence | 23.x or later |

**UVM library:** IEEE 1800.2 UVM (version 1.2 or 2.0). Most commercial simulators ship with a built-in UVM library. If yours does not, download the reference implementation from Accellera.

**What Path B enables over Path A:**

| Capability | Path A (cocotb/pyuvm) | Path B (SV UVM) |
|------------|----------------------|-----------------|
| Constrained random | Python `random` / manual constraints | Native `rand`, `constraint`, `randomize()` with solver |
| UVM factory & config_db | pyuvm (Python reimplementation) | Native SV UVM class library |
| Functional coverage | cocotb-coverage (Python API) | Native `covergroup`, `coverpoint`, `cross` |
| Assertions | cocotb timing checks (limited) | Full SVA (`|->`, `|=>`, `##N`, `[*N]`, `throughout`, `$rose`, `$fell`, etc.) |
| Transaction recording | Manual logging | Built-in transaction databases (FSDB, VPD) |
| Constrained-random solver | No solver (manual constraint logic) | Built-in constraint solver with `dist`, `inside`, `solve before` |
| Debug | VCD + GTKWave/Surfer | Full waveform DB (FSDB/VPD) + Verdi/Visualizer |

**Quick start (Path B — VCS example):**

```bash
# Compile UVM testbench with VCS
vcs -sverilog -ntb_opts uvm-1.2 \
    +incdir+duts/common \
    duts/common/dv_common_pkg.sv \
    duts/nexus_uart/nexus_uart.sv \
    tb/nexus_uart_tb_top.sv \
    -cm line+branch+toggle+fsm+cond \
    -o simv

# Run simulation
./simv +UVM_TESTNAME=nexus_uart_base_test \
    -cm line+branch+toggle+fsm+cond

# Generate coverage report
urg -dir simv.vdb -report coverage_report
```

**Quick start (Path B — Questa example):**

```bash
# Compile
vlib work
vlog -sv +incdir+duts/common \
    duts/common/dv_common_pkg.sv \
    duts/nexus_uart/nexus_uart.sv \
    tb/nexus_uart_tb_top.sv

# Run with UVM and coverage
vsim -c -coverage -voptargs="+cover=bcestf" \
    work.nexus_uart_tb_top \
    +UVM_TESTNAME=nexus_uart_base_test \
    -do "coverage save -onexit coverage.ucdb; run -all; quit"

# Generate report
vcover report coverage.ucdb -output coverage_report.txt
```

### Path B Submission Requirements

If you choose Path B, your submission must include:

1. A `Makefile` with targets for your chosen simulator:
   ```makefile
   # Required targets
   sim_vcs:      # Build and run with VCS
   sim_questa:   # Build and run with Questa
   sim_verilator: # Fallback open-source run (best effort)
   coverage:     # Generate coverage reports
   ```

2. Set `simulator` in your `metadata.yaml` to `vcs`, `questa`, or `xcelium`.

3. **Strongly recommended:** Include a `cocotb_wrapper/` directory with a minimal cocotb-based test that exercises core functionality. This serves as a fallback if the commercial simulator is temporarily unavailable during evaluation.

4. All SystemVerilog UVM source files under `testbench/` with a clear package structure:
   ```
   testbench/
   ├── tb_top.sv              — Top-level testbench module
   ├── env/
   │   ├── my_env_pkg.sv      — Environment package
   │   ├── my_env.sv          — UVM environment class
   │   └── my_scoreboard.sv   — Scoreboard with reference model
   ├── agents/
   │   ├── tl_ul_agent_pkg.sv — TL-UL agent package
   │   ├── tl_ul_driver.sv
   │   ├── tl_ul_monitor.sv
   │   ├── tl_ul_sequencer.sv
   │   └── tl_ul_seq_lib.sv   — Sequence library
   ├── tests/
   │   ├── test_pkg.sv        — Test package
   │   └── my_base_test.sv    — Base test class
   └── coverage/
       └── my_coverage.sv     — Covergroups and functional coverage
   ```

### Mixing Paths

You may use Path A for some DUTs and Path B for others. Each submission is independent — declare the simulator in that submission's `metadata.yaml`. You may also transition from Path A to Path B mid-competition if you gain access to commercial tools.

### Optional Tools (Both Paths)

| Tool | Version | Purpose |
|------|---------|---------|
| SymbiYosys + Yosys | latest | Formal verification and property checking |
| sv2v | latest | SystemVerilog to Verilog conversion (if Icarus has issues) |
| GTKWave / Surfer | latest | Waveform viewing (VCD/FST) |
| Verdi (Synopsys) | — | Waveform and debug (Path B, VCS) |
| Visualizer (Siemens) | — | Waveform and debug (Path B, Questa) |
| SimVision (Cadence) | — | Waveform and debug (Path B, Xcelium) |

---

## 3. DUT Overview

The seven DUTs are organized into four difficulty tiers. Scoring weights scale with tier to reward tackling harder designs.

### Tier 1 -- Starter (1x scoring weight)

| DUT | Description |
|-----|-------------|
| **nexus_uart** | UART controller supporting configurable baud rate, 8N1 framing, TX/RX FIFOs, parity options, and break detection. Good entry point for learning the TL-UL interface and building basic agents. |
| **bastion_gpio** | General-purpose I/O controller with per-pin direction control, interrupt generation on edge/level events, and output data register. Straightforward register-driven behavior. |

### Tier 2 -- Intermediate (1.5x scoring weight)

| DUT | Description |
|-----|-------------|
| **warden_timer** | Timer and watchdog module with multiple 64-bit timer channels, programmable prescaler, compare registers, and interrupt/reset generation on timeout. Requires careful timing verification. |
| **citadel_spi** | SPI host controller supporting all four SPI modes (CPOL/CPHA), configurable clock divider, chip-select management, and TX/RX FIFOs. Protocol-level verification required. |

### Tier 3 -- Advanced (2x scoring weight)

| DUT | Description |
|-----|-------------|
| **aegis_aes** | AES-128 encryption/decryption engine with ECB and CBC modes, key expansion logic, and side-channel countermeasures. Requires cryptographic reference models and data-path verification. |
| **sentinel_hmac** | HMAC-SHA256 accelerator with streaming message input, configurable key length, and digest output. Multi-block message handling and padding logic add complexity. |

### Tier 4 -- Expert (2.5x scoring weight)

| DUT | Description |
|-----|-------------|
| **rampart_i2c** | I2C host and target controller supporting standard (100 kHz) and fast (400 kHz) modes, clock stretching, multi-master arbitration, repeated starts, and NACK handling. The most complex DUT in the competition, requiring both host-mode and target-mode verification with protocol-level edge cases. |

---

## 4. Common Interface: TL-UL Bus

All DUTs use a simplified TileLink Uncached Lightweight (TL-UL) bus interface for register access. Building a reusable TL-UL agent is strongly recommended -- it works for every DUT in the competition.

### Channel A (Host to Device)

| Signal | Width | Description |
|--------|-------|-------------|
| `a_valid` | 1 | Transaction request valid |
| `a_ready` | 1 | Device ready to accept |
| `a_opcode` | 3 | Operation type |
| `a_address` | 32 | Target register address |
| `a_data` | 32 | Write data |
| `a_mask` | 4 | Byte-lane enables |
| `a_source` | 8 | Transaction source ID |
| `a_size` | 2 | Transfer size (log2 bytes) |

### Channel D (Device to Host)

| Signal | Width | Description |
|--------|-------|-------------|
| `d_valid` | 1 | Response valid |
| `d_ready` | 1 | Host ready to accept |
| `d_opcode` | 3 | Response type |
| `d_data` | 32 | Read data |
| `d_source` | 8 | Matching source ID |
| `d_error` | 1 | Error indicator |

### Opcodes

| Name | Value | Direction | Description |
|------|-------|-----------|-------------|
| `PutFullData` | 0 | A | Full-word write |
| `PutPartialData` | 1 | A | Partial write (uses mask) |
| `Get` | 4 | A | Read request |
| `AccessAck` | 0 | D | Write acknowledgment |
| `AccessAckData` | 1 | D | Read response with data |

### Handshake Protocol

Transfers occur on the rising edge of `clk_i` when both `valid` and `ready` are asserted on the same channel. The host must hold Channel A signals stable while `a_valid` is high and `a_ready` is low.

### Standard Signals

Every DUT also exposes:

| Signal | Description |
|--------|-------------|
| `clk_i` | Clock input |
| `rst_ni` | Active-low synchronous reset |
| `intr_o` | Interrupt output (active-high, width varies per DUT) |
| `alert_o` | Alert/fault output |

---

## 5. How to Build and Run

### Path A — cocotb (Open-Source)

#### Compiling with Verilator

```bash
verilator --cc --coverage \
    duts/common/dv_common_pkg.sv \
    duts/<dut_name>/<dut_name>.sv
```

Add `--trace` if you need VCD waveform output for debugging.

#### Compiling with Icarus Verilog

```bash
iverilog -g2012 -o sim \
    duts/common/dv_common_pkg.sv \
    duts/<dut_name>/<dut_name>.sv
```

#### Running cocotb Tests

Each testbench uses a `Makefile` that sets three key variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `TOPLEVEL` | Top-level RTL module name | `nexus_uart` |
| `MODULE` | Python test module(s) | `test_uart_basic` |
| `SIM` | Simulator selection | `verilator` or `icarus` |

Run tests with:

```bash
# Using Verilator
make SIM=verilator MODULE=test_uart_basic TOPLEVEL=nexus_uart

# Using Icarus Verilog
make SIM=icarus MODULE=test_uart_basic TOPLEVEL=nexus_uart
```

#### Collecting Coverage (Path A)

Generate code coverage data with Verilator:

```bash
# Compile with coverage enabled
verilator --cc --coverage --coverage-line --coverage-toggle \
    duts/common/dv_common_pkg.sv \
    duts/<dut_name>/<dut_name>.sv

# After simulation, process coverage data
verilator_coverage --annotate coverage_annotated/ coverage.dat
verilator_coverage --write-info coverage.info coverage.dat
```

Functional coverage is collected via `cocotb-coverage` or `pyuvm` covergroups in your Python testbench.

### Path B — SystemVerilog UVM (Commercial Simulators)

#### VCS

```bash
# Compile
vcs -sverilog -ntb_opts uvm-1.2 \
    +incdir+duts/common +incdir+testbench/env +incdir+testbench/agents \
    duts/common/dv_common_pkg.sv \
    duts/<dut_name>/<dut_name>.sv \
    testbench/agents/tl_ul_agent_pkg.sv \
    testbench/env/my_env_pkg.sv \
    testbench/tests/test_pkg.sv \
    testbench/tb_top.sv \
    -cm line+branch+toggle+fsm+cond \
    -o simv

# Run
./simv +UVM_TESTNAME=my_base_test -cm line+branch+toggle+fsm+cond

# Coverage report
urg -dir simv.vdb -report coverage_html
```

#### Questa

```bash
# Compile
vlib work
vlog -sv +incdir+duts/common +incdir+testbench/env +incdir+testbench/agents \
    duts/common/dv_common_pkg.sv \
    duts/<dut_name>/<dut_name>.sv \
    testbench/agents/tl_ul_agent_pkg.sv \
    testbench/env/my_env_pkg.sv \
    testbench/tests/test_pkg.sv \
    testbench/tb_top.sv

# Run with coverage
vsim -c -coverage -voptargs="+cover=bcestf" \
    work.tb_top +UVM_TESTNAME=my_base_test \
    -do "coverage save -onexit coverage.ucdb; run -all; quit"

# Coverage report
vcover report coverage.ucdb -output coverage_report.txt -details
```

#### Xcelium

```bash
# Compile and run
xrun -sv -uvm -access +rwc \
    +incdir+duts/common +incdir+testbench/env +incdir+testbench/agents \
    duts/common/dv_common_pkg.sv \
    duts/<dut_name>/<dut_name>.sv \
    testbench/agents/tl_ul_agent_pkg.sv \
    testbench/env/my_env_pkg.sv \
    testbench/tests/test_pkg.sv \
    testbench/tb_top.sv \
    +UVM_TESTNAME=my_base_test \
    -coverage all -covoverwrite

# Coverage report
imc -load cov_work/scope/test -report -metrics -out coverage_report.txt
```

#### Writing a SystemVerilog UVM Testbench

A minimal UVM testbench for these DUTs requires:

1. **TL-UL Agent** — A reusable UVM agent with:
   - `tl_ul_seq_item` extending `uvm_sequence_item` with `rand` fields for address, data, opcode
   - `tl_ul_driver` extending `uvm_driver` that drives the TL-UL A-channel and waits for D-channel response
   - `tl_ul_monitor` extending `uvm_monitor` with analysis port for observed transactions
   - `tl_ul_sequencer`, `tl_ul_agent`, and a sequence library

2. **Environment** — `uvm_env` subclass instantiating the agent, scoreboard, and coverage collector

3. **Scoreboard** — `uvm_scoreboard` with a reference model that predicts expected DUT behavior

4. **Coverage** — `covergroup` definitions for the DUT's key behaviors (see the spec for guidance on what to cover)

5. **Testbench top** — Module that instantiates the DUT, generates clock/reset, and connects the UVM agent interface

Example `tb_top.sv` structure:
```systemverilog
module tb_top;
  import uvm_pkg::*;
  import dv_common_pkg::*;
  import test_pkg::*;

  logic clk, rst_n;
  tl_a_pkt_t tl_a;
  logic       tl_a_ready;
  tl_d_pkt_t tl_d;
  logic       tl_d_ready;
  // DUT-specific signals...

  // Clock generation
  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  // Reset sequence
  initial begin
    rst_n = 0;
    repeat (10) @(posedge clk);
    rst_n = 1;
  end

  // DUT instantiation
  nexus_uart u_dut (
    .clk_i      (clk),
    .rst_ni     (rst_n),
    .tl_i       (tl_a),
    .tl_i_ready (tl_a_ready),
    .tl_o       (tl_d),
    .tl_o_ready (tl_d_ready),
    // DUT-specific ports...
  );

  // Connect virtual interface and run UVM
  initial begin
    // Pass interface handles to UVM via config_db
    uvm_config_db#(virtual tl_ul_if)::set(null, "*", "tl_vif", u_tl_if);
    run_test();
  end
endmodule
```

#### Collecting Coverage (Path B)

Commercial simulators provide unified coverage databases:

| Simulator | Coverage DB | Merge Tool | Report Tool |
|-----------|------------|------------|-------------|
| VCS | `.vdb` directory | `urg -dir *.vdb` | `urg -report` |
| Questa | `.ucdb` file | `vcover merge` | `vcover report` |
| Xcelium | `cov_work/` directory | `imc -load -merge` | `imc -report` |

All three support line, branch, toggle, FSM, condition, and functional coverage (covergroups). Export coverage reports as HTML or text in your `results/` directory.

#### SVA Assertions (Path B Advantage)

One major advantage of Path B is full SVA support. Example assertions for the TL-UL protocol:

```systemverilog
// Request must be held stable until accepted
property tl_a_stable;
  @(posedge clk) disable iff (!rst_n)
  (tl_a.a_valid && !tl_a_ready) |=> ($stable(tl_a.a_address) && $stable(tl_a.a_data));
endproperty
assert property (tl_a_stable);

// Every request gets a response
property tl_response;
  @(posedge clk) disable iff (!rst_n)
  (tl_a.a_valid && tl_a_ready) |-> ##[1:20] (tl_d.d_valid && tl_d_ready);
endproperty
assert property (tl_response);
```

cocotb-based testbenches (Path A) can also include SVA assertions via Verilog bind files that are compiled alongside the DUT.

### No Pre-Built Environment Provided

Participants are responsible for setting up their own simulation environment. We recommend:

- **Local setup**: Install Icarus Verilog + cocotb via your OS package manager and pip. This is the fastest path for Path A.
- **[EDA Playground](https://www.edaplayground.com/)**: Free online platform with access to commercial simulators (VCS, Riviera-PRO). Useful for quick experiments and for teams without local commercial licenses.
- **University EDA licenses**: Many universities have site licenses for VCS, Questa, or Xcelium. Check with your department's CAD administrators.
- **Cloud EDA**: Services like Synopsys Cloud or AWS with EDA AMIs can provide commercial tools on-demand.

The competition GitHub repository contains all RTL, specs, and starter code. Clone it and you're ready to start.

---

## 6. Submission Format

Every submission must follow the directory structure for your chosen path. The automated evaluation pipeline validates these strictly.

**For the exact file requirements per task** (required files, YAML schemas, naming conventions, automated checks), see the [Submission Requirements](submission_requirements.md) document.

### Path A Submission (cocotb / pyuvm)

```
submission-{task_id}-{dut_id}/
├── testbench/
│   ├── env.py                — Top-level environment
│   ├── agents/               — Driver, monitor, sequencer per agent
│   ├── scoreboard.py         — Reference model + comparison logic
│   ├── coverage.py           — Coverage model definition
│   ├── sequences/            — Test sequences
│   └── assertions/           — SVA bind files (optional)
├── tests/
│   └── test_*.py             — Test files (must follow test_* naming)
├── results/
│   ├── coverage_report.html  — Coverage summary
│   ├── regression_log.txt    — Full regression output
│   └── bug_reports/          — Bug report files (if bugs found)
├── methodology.md            — REQUIRED: How AI was used
├── Makefile                  — Build and run instructions
└── metadata.yaml             — Team info, task/DUT ID
```

### Path B Submission (SystemVerilog UVM)

```
submission-{task_id}-{dut_id}/
├── testbench/
│   ├── tb_top.sv             — Top-level testbench module
│   ├── env/
│   │   ├── my_env_pkg.sv     — Environment package
│   │   ├── my_env.sv         — UVM environment
│   │   └── my_scoreboard.sv  — Scoreboard with reference model
│   ├── agents/
│   │   ├── tl_ul_agent_pkg.sv
│   │   ├── tl_ul_driver.sv
│   │   ├── tl_ul_monitor.sv
│   │   ├── tl_ul_sequencer.sv
│   │   ├── tl_ul_seq_lib.sv  — Sequence library
│   │   └── tl_ul_if.sv       — Virtual interface definition
│   ├── tests/
│   │   ├── test_pkg.sv       — Test package
│   │   └── my_base_test.sv   — Base test class
│   ├── coverage/
│   │   └── my_coverage.sv    — Covergroups
│   └── assertions/
│       └── my_assertions.sv  — SVA bind module
├── cocotb_wrapper/ (recommended)
│   ├── Makefile              — Fallback cocotb run
│   └── test_fallback.py     — Minimal cocotb test exercising core functionality
├── tests/
│   └── test_list.yaml        — List of UVM test names to run
├── results/
│   ├── coverage_report.html
│   ├── regression_log.txt
│   └── bug_reports/
├── methodology.md            — REQUIRED: How AI was used
├── Makefile                  — Build and run instructions (sim_vcs / sim_questa targets)
└── metadata.yaml             — Team info, task/DUT ID, simulator choice
```

### metadata.yaml Format

```yaml
team_name: "your-team-name"
task_id: "task-xxx"
dut_id: "nexus_uart"
simulator: "verilator"    # or "vcs", "questa", "xcelium", "icarus"
# Path A fields:
python_version: "3.11"
cocotb_version: "1.9.0"
# Path B fields (if applicable):
uvm_version: "1.2"
sv_standard: "1800-2017"
timestamp: "2026-03-30T12:00:00Z"
```

---

## 7. methodology.md Requirements

Every submission **must** include a `methodology.md` file. Submissions without this file will receive a zero on the methodology component (20% of total score). Cover the following sections:

### 1. AI Tools Used

List every AI tool, model, and version used. Include LLMs, code assistants, and any AI-powered analysis tools.

### 2. Prompt Engineering Strategies

Describe the prompting techniques that worked best. Include representative prompt examples (sanitized if needed). Discuss how you structured prompts for different tasks (agent generation, sequence creation, coverage analysis).

### 3. Iteration Process

Document how many LLM interactions were required, how feedback loops worked, and how you guided the AI from initial output to final testbench. Include the number of major iterations per component.

### 4. Human vs AI Contribution Breakdown

Provide an honest estimate (percentage) of human versus AI contribution for each component: environment architecture, driver/monitor code, sequences, scoreboard, coverage model, and debugging.

### 5. Failed Approaches

Describe approaches that did not work and why. This section is valued -- it demonstrates depth of exploration and provides useful data for the research community.

### 6. Efficiency Metrics

Report approximate token usage, number of API calls, wall-clock time, and estimated cost. This data helps the community understand the practical economics of AI-assisted verification.

### 7. Reproducibility Notes

Describe how another team could reproduce your workflow. Include tool versions, model versions, and any configuration details needed to replicate your results.

### 8. LLM Conversation Evidence (Required)

You **must** provide verifiable evidence of your LLM/agent interactions. Include **at least one** of the following:

- **Shareable conversation link** — If your LLM platform supports it (e.g., ChatGPT share links, Claude.ai shared conversations), include the direct URL. This is the preferred method as it provides full context.
- **Exported conversation log** — A `prompts/` directory in your submission containing text or markdown files with the key prompts you used and the LLM's responses. Include at minimum: the 5 most impactful prompts that shaped your verification environment, and any prompts involved in debugging or coverage closure.
- **Agent execution log** — If you built an agentic system, include the full agent trace as `agent_log.json` (see Phase 4 format) showing each LLM call, the prompt, the response summary, and the action taken.

**Why this matters:** This competition evaluates how effectively teams leverage AI. Judges cannot assess AI integration quality without seeing the actual interactions. Teams that provide richer evidence of their AI workflow will score higher on the AI Integration pillar (20% of total score). Submissions without any conversation evidence will receive at most half credit on the AI Integration component.

**Privacy note:** You may redact API keys, personal information, or proprietary prompts. The goal is to show the *nature* and *quality* of AI interaction, not to expose sensitive details.

---

## 8. Evaluation Process

### Automated Evaluation

Submissions are collected periodically from the platform and processed through an automated evaluation pipeline:

1. **Structure validation** -- Verifies that the submission follows the required directory layout and contains all mandatory files.
2. **Compilation check** -- Builds the testbench with both Verilator and Icarus Verilog. Both must succeed.
3. **Simulation run** -- Executes the full test suite with a 10-minute timeout. Tests that exceed this limit are terminated and scored as incomplete.
4. **Coverage measurement** -- Collects line, branch, toggle, FSM, and functional coverage metrics from the simulation results.
5. **Bug detection** -- Runs the testbench against a set of hidden buggy RTL variants. Each variant contains a specific injected bug. Testbenches that detect more bugs score higher.
6. **Score computation** -- Combines all metrics into a final score using the published rubric and tier-based weighting.

### Judge Evaluation

Periodically, a panel of judges reviews submissions for qualitative factors:

- **Code quality and methodology review** -- Readability, structure, reuse, and adherence to verification best practices.
- **AI integration innovation assessment** -- Novel or particularly effective uses of AI in the verification workflow.
- **Innovation assessment** -- Outstanding submissions may receive additional recognition at the discretion of the evaluation panel.

### Results

Evaluation is run **twice** during the competition:

| Evaluation | Timing | Scope | Results |
|-----------|--------|-------|---------|
| **Mid-competition** | ~Day 4 (Apr 3) | Phases 1-2 submissions | Top 10 teams posted to leaderboard |
| **Final** | Day 8 (Apr 8, within 24 hrs of close) | All phases, all submissions | Full leaderboard + awards |

Leaderboard scores are updated manually by the organizers after each evaluation cycle. Teams can track their submissions on the competition platform.

---

## 9. Coverage Measurement

### Coverage Types

| Type | Path A Tool | Path B Tool | Description |
|------|-------------|-------------|-------------|
| Line | Verilator | VCS/Questa/Xcelium | Percentage of RTL source lines exercised |
| Branch | Verilator | VCS/Questa/Xcelium | Percentage of conditional branches taken |
| Toggle | Verilator | VCS/Questa/Xcelium | Percentage of signals that toggled 0-to-1 and 1-to-0 |
| FSM | Verilator | VCS/Questa/Xcelium | Percentage of FSM states and transitions visited |
| Condition | — | VCS/Questa/Xcelium | Percentage of Boolean sub-expression combinations (Path B only) |
| Functional | cocotb-coverage / pyuvm | SV `covergroup` | User-defined coverpoints and crosses |

### Coverage Targets

| Metric | Target | Baseline (reference_tb) |
|--------|--------|------------------------|
| Line | 90% | ~40% |
| Branch | 85% | ~30% |
| Toggle | 80% | ~25% |
| FSM States | 100% | varies |
| Functional | 85% | ~20% |

The baseline numbers reflect what the provided `reference_tb/` testbenches achieve. Your goal is to close the gap between the baseline and the targets. Coverage closure is the primary differentiator between competitive submissions.

---

## 10. Tips for Success

1. **Start with Tier 1 DUTs to learn the environment.** The `nexus_uart` and `bastion_gpio` designs are intentionally simpler so you can master the toolchain, TL-UL interface, and submission workflow before moving to harder targets.

2. **Read the specification carefully.** Some requirements are subtle and easy to miss. Corner cases buried in the spec are often the difference between 80% and 95% coverage.

3. **Use AI iteratively.** The most effective workflow is a tight loop: generate code, compile, fix errors, run tests, analyze coverage gaps, then generate more targeted tests. Avoid generating everything in one shot.

4. **Build reusable components.** A well-built TL-UL bus agent, register abstraction layer, and scoreboard base class work for every DUT. Invest time in these once, then reuse across all submissions.

5. **Focus on coverage closure.** Coverage is the primary differentiator in scoring. After achieving basic functionality, spend the majority of your effort closing coverage gaps -- especially branch and functional coverage.

6. **Document your AI methodology thoroughly.** The `methodology.md` accounts for 20% of your total score. A well-documented process with honest reporting of failures is valued more than a polished narrative.

7. **Test with your target simulator early.** Path A submissions should compile with both Verilator and Icarus. Path B submissions should compile cleanly with your chosen commercial simulator. If using Path B, also test your `cocotb_wrapper/` fallback.

8. **Use the verification plans.** The `vplans/` directory contains YAML-formatted verification plans that list every feature and scenario to cover. Use them as a checklist to ensure completeness.

9. **Look at the CSR maps.** The `csr_maps/` Hjson files define every register, field, reset value, and access type. Use them to auto-generate register tests and ensure full register coverage.

10. **Submit early and often.** Multiple submissions are allowed, and only your highest score counts. Early submissions give you feedback from the automated pipeline that you can use to improve.

---

## 11. Known Simulator Notes

| DUT | Icarus Verilog | Verilator | VCS / Questa / Xcelium |
|-----|---------------|-----------|------------------------|
| bastion_gpio | Works | Works | Works |
| nexus_uart | Works | Works | Works |
| warden_timer | Works | Works | Works |
| citadel_spi | Works | Works | Works |
| sentinel_hmac | Works | Works | Works |
| rampart_i2c | Works | Works | Works |
| aegis_aes | Hang (see below) | Works | Works |

**aegis_aes on Icarus Verilog**: The AES design uses unpacked arrays (`logic [31:0] key_schedule [44]`) in combinational logic that triggers an Icarus sensitivity-list issue, causing the simulation to hang. This is a known Icarus Verilog limitation with SystemVerilog unpacked arrays in `always_comb` blocks. **Workarounds**: use Verilator (`make SIM=verilator`) or a commercial simulator (`make SIM=vcs`). This does not affect the other 6 DUTs.

All DUTs compile cleanly with `iverilog -g2012` — the issue is simulation-time only.

---

## 12. RTL Disclaimer

The RTL designs provided are modified versions of open-source IP blocks, created exclusively for this competition. They are not production-quality, not security-reviewed, and must not be used outside of this competition context. Signal names and internal architectures have been modified from their original sources.

---

## 13. Frequently Asked Questions

**Q: Can I use any LLM or AI tool?**
A: Yes. You may use any publicly available or commercial LLM, code assistant, or AI-powered tool. The only requirement is that you document every tool used in your `methodology.md` file.

**Q: Can I submit multiple times for the same DUT?**
A: Yes. You can submit as many times as you like. Only your highest-scoring submission for each DUT will count toward your final ranking.

**Q: Can I modify the RTL source files?**
A: No. The RTL under `duts/` must not be modified. You may only build verification environments around the provided designs. Submissions that include modified RTL will be disqualified.

**Q: When are results posted to the leaderboard?**
A: Evaluation runs twice: a mid-competition evaluation around Day 4 (top 10 posted) and a final evaluation within 24 hours of the competition close. Results and leaderboard are updated on the platform after each evaluation.

**Q: Can I use commercial simulators (VCS, Questa, Xcelium)?**
A: Yes. The competition fully supports commercial simulators as **Path B**. You may build full SystemVerilog UVM testbenches and submit them targeting VCS, Questa, or Xcelium. Set `simulator` in your `metadata.yaml` accordingly. We strongly recommend also including a `cocotb_wrapper/` with a minimal open-source fallback test.

**Q: Which path should I choose — Path A (cocotb) or Path B (SV UVM)?**
A: It depends on your team. Path A is easier to set up (no licenses needed), has starter code provided, and is sufficient to score well. Path B gives you access to more powerful verification features (native constrained-random, full SVA, SystemVerilog covergroups) but requires commercial tool access. Teams with industry DV experience and tool licenses will likely prefer Path B. Teams new to verification should start with Path A.

**Q: Can I mix Path A and Path B across different DUTs?**
A: Yes. Each submission is independent. You can submit a cocotb testbench for `nexus_uart` and a SystemVerilog UVM testbench for `aegis_aes`. Declare the simulator in each submission's `metadata.yaml`.

**Q: Do I need to submit for every DUT?**
A: No. You can submit for as many or as few DUTs as you choose. However, submitting for higher-tier DUTs with their increased scoring weights is the fastest path to a top leaderboard position.

**Q: Can I collaborate with other teams?**
A: Each registered team works independently. Sharing testbench code, coverage results, or bug findings between teams is not permitted. You may discuss general AI prompting strategies publicly, but not DUT-specific solutions.

**Q: What happens if my tests exceed the 10-minute timeout?**
A: Tests that do not complete within 10 minutes are terminated. Partial results up to the timeout are used for scoring, but incomplete test suites will generally score lower. Optimize your test runtime by focusing on targeted, high-value tests rather than exhaustive random simulation.

**Q: What file formats are accepted for bug reports?**
A: Bug reports should be placed in `results/bug_reports/` as markdown files. Each file should describe the bug, the failing test, expected versus actual behavior, and the relevant register or signal values. Clear, well-structured bug reports contribute to your score.

**Q: Does choosing Path B give me a scoring advantage over Path A?**
A: No. Both paths are evaluated on the same metrics (coverage, bug detection, code quality). Path B gives you more powerful tools (constrained-random, SVA, native covergroups), which may help you achieve higher coverage more efficiently — but the scoring itself is path-neutral. A well-crafted cocotb testbench can score just as highly as a UVM one.

**Q: How is the final score calculated?**
A: The final score combines automated metrics (coverage, bug detection, compilation success) weighted at 80% and judge evaluation (code quality, methodology, AI innovation) weighted at 20%. Within the automated portion, coverage closure is the largest single factor. Tier-based scoring weights (1x through 2.5x) are applied to each DUT's raw score.
