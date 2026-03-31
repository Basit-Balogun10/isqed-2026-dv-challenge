# Agentic AI Design Verification Challenge 2026

**ISQED 2026 | March 31 -- April 7, 2026**

A week-long competition where teams build AI-assisted verification environments for real-complexity RTL designs derived from the OpenTitan ecosystem. Participants develop testbenches, drive coverage closure, debug failures, and build autonomous verification agents.

> **This is a Design Verification competition** -- not a security CTF. The battlefield is testbenches, coverage models, constrained-random stimulus, assertions, and the relentless grind toward coverage closure.

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/<org>/isqed-2026-dv-challenge.git
cd isqed-2026-dv-challenge

# Verify your toolchain (Path A -- open-source)
iverilog -g2012 -o /dev/null duts/common/dv_common_pkg.sv duts/nexus_uart/nexus_uart.sv

# Install cocotb
pip install cocotb cocotb-bus cocotb-coverage

# Run a skeleton testbench
cd skeleton_envs/nexus_uart
make SIM=icarus
```

All DUTs use **flat TL-UL signals** (no packed structs) for maximum simulator compatibility. See the [Instructions & Documentation](platform_content/instructions_and_documentation.md) for the full TL-UL signal list.

No pre-built environments are provided. Participants set up their own tools. Teams without local EDA tools may use [EDA Playground](https://www.edaplayground.com/) for free access to commercial simulators.

---

## Competition Structure

| Phase | Title | Window | Duration |
|-------|-------|--------|----------|
| **Phase 1** | Verification Environment Construction | Mar 31 -- Apr 2 | 72 hrs |
| **Phase 2** | Coverage Closure Campaign | Apr 2 -- Apr 4 | 48 hrs |
| **Phase 3** | Debug & Root-Cause Analysis | Apr 4 -- Apr 5 | 36 hrs |
| **Phase 4** | Agentic Verification Pipeline | Apr 5 -- Apr 7 | 36 hrs |

Phases overlap slightly -- you can start Phase N+1 while finishing Phase N.

---

## DUT Portfolio

Seven designs of increasing complexity, all using a common TileLink-UL bus interface:

| DUT | Tier | Description | Scoring Weight |
|-----|------|-------------|----------------|
| [`nexus_uart`](duts/nexus_uart/) | Starter | Full-duplex UART with FIFOs, parity, loopback | 1.0x |
| [`bastion_gpio`](duts/bastion_gpio/) | Starter | 32-pin GPIO with edge detection, masked writes | 1.0x |
| [`warden_timer`](duts/warden_timer/) | Intermediate | 64-bit timer + watchdog with bark/bite | 1.5x |
| [`citadel_spi`](duts/citadel_spi/) | Intermediate | SPI host, 4 modes, segment-based commands | 1.5x |
| [`aegis_aes`](duts/aegis_aes/) | Advanced | AES-128 ECB/CBC encrypt/decrypt engine | 2.0x |
| [`sentinel_hmac`](duts/sentinel_hmac/) | Advanced | HMAC-SHA256 with streaming message FIFO | 2.0x |
| [`rampart_i2c`](duts/rampart_i2c/) | Expert | Dual-role I2C host/target, multi-master, clock stretching | 2.5x |

---

## Tasks

### Phase 1 -- Verification Environment Construction

| Task | Name | Max Points | Description |
|------|------|-----------|-------------|
| [1.1](platform_content/tasks/task_1_1_interface_agents.md) | Interface Agent Generation | 900 | Build bus and protocol agents (driver, monitor, scoreboard) |
| [1.2](platform_content/tasks/task_1_2_vplan_test_suite.md) | Verification Plan to Test Suite | 1200 | Generate tests from YAML verification plans |
| [1.3](platform_content/tasks/task_1_3_csr_verification.md) | Register Verification Suite | 200 | Auto-generate CSR regression tests from Hjson maps |
| [1.4](platform_content/tasks/task_1_4_assertion_library.md) | Assertion Library | 700 | Write assertions that catch bugs without false positives |

### Phase 2 -- Coverage Closure Campaign

| Task | Name | Max Points | Description |
|------|------|-----------|-------------|
| [2.1](platform_content/tasks/task_2_1_coverage_gap_analysis.md) | Coverage Gap Analysis | 200 | Analyze and prioritize uncovered regions |
| [2.2](platform_content/tasks/task_2_2_stimulus_engineering.md) | Stimulus Engineering | 2000 | Write tests to close coverage gaps |
| [2.3](platform_content/tasks/task_2_3_coverage_directed_generation.md) | Coverage-Directed Test Generation | 300 | Build an adaptive AI-in-the-loop CDG system |

### Phase 3 -- Debug & Root-Cause Analysis

| Task | Name | Max Points | Description |
|------|------|-----------|-------------|
| [3.1](platform_content/tasks/task_3_1_log_whisperer.md) | The Log Whisperer | 300 | Triage simulation failures from logs |
| [3.2](platform_content/tasks/task_3_2_trace_detective.md) | The Trace Detective | 400 | Waveform-guided debug and root-cause tracing |
| [3.3](platform_content/tasks/task_3_3_regression_medic.md) | The Regression Medic | 300 | Bucket failures, validate patches |

### Phase 4 -- Agentic Verification Pipeline

| Task | Name | Max Points | Description |
|------|------|-----------|-------------|
| [4.1](platform_content/tasks/task_4_1_autoverifier.md) | The AutoVerifier | 1000 | Build an autonomous end-to-end verification agent |
| [4.2](platform_content/tasks/task_4_2_regression_agent.md) | The Regression Agent | 600 | CI/CD verification agent for RTL commit streams |
| [4.3](platform_content/tasks/task_4_3_spec_interpreter.md) | The Spec Interpreter | 500 | Generate verification plans from specs alone |

**Total possible: ~8,600+ points**

---

## Repository Contents

```
├── duts/                  RTL source (SystemVerilog) for all 7 DUTs
│   └── common/            Shared TL-UL bus interface package
├── specs/                 Specification documents per DUT (markdown)
├── csr_maps/              Register maps in Hjson format
├── vplans/                Verification plans per DUT (YAML)
├── skeleton_envs/         Starter cocotb testbenches with TL-UL agent
├── phase3_materials/      Debug & root-cause analysis inputs (Phase 3)
│   ├── task_3_1_logs/     10 simulation failure logs
│   ├── task_3_2_traces/   5 failure traces with signal data
│   └── task_3_3_regression/  Regression suite (200 tests, 35 failing, 5 patches)
└── platform_content/      Competition docs and task descriptions
    ├── competition_rules.md
    ├── instructions_and_documentation.md
    ├── submission_requirements.md
    ├── evaluation/        Scoring rubrics
    └── tasks/             Extended task descriptions (linked above)
```

---

## Two Verification Paths

| | Path A (Open-Source) | Path B (Commercial) |
|---|---|---|
| **Simulator** | Verilator + Icarus Verilog | VCS / Questa / Xcelium |
| **Testbench** | cocotb + pyuvm (Python) | SystemVerilog UVM |
| **Coverage** | cocotb-coverage | Native SV covergroups |
| **Assertions** | SVA via bind files | Full SVA support |
| **Constrained Random** | Manual / Python random | Native solver (`rand`, `constraint`) |
| **Starter code** | Provided | Build your own |
| **License needed** | No | Yes |

Both paths are fully supported and scored identically. See the [Instructions](platform_content/instructions_and_documentation.md) for setup details.

---

## Submission

Submissions are made through the **competition website** (linked from the ISQED 2026 event page). Multiple submissions per task are allowed -- only your highest score counts.

Each submission must include a `methodology.md` documenting your AI usage (20% of score).

**Key documents:**
- [Competition Rules](platform_content/competition_rules.md) -- Eligibility, timeline, policies
- [Instructions & Documentation](platform_content/instructions_and_documentation.md) -- Toolchain setup, build/run, both verification paths
- [Submission Requirements](platform_content/submission_requirements.md) -- **Exact files, formats, and naming conventions per task**
- [Evaluation Rubrics](platform_content/evaluation/evaluation_rubrics.md) -- Detailed scoring breakdown

---

## Scoring

| Pillar | Weight | Measured By |
|--------|--------|-------------|
| **Correctness** | 30% | Bug detection rate, false positive rate (automated) |
| **Coverage** | 30% | Line, branch, toggle, FSM, functional coverage (automated) |
| **Methodology** | 20% | Code quality, architecture, verification best practices (judges) |
| **AI Integration** | 20% | Innovation and effectiveness of AI usage (judges) |

Full scoring rubric: [evaluation_rubrics.md](platform_content/evaluation/evaluation_rubrics.md)

---

## RTL Disclaimer

The RTL designs provided in this repository are modified versions of open-source IP blocks, created exclusively for this competition. They are not production-quality, not security-reviewed, and must not be used outside of this competition context. Signal names and internal architectures have been modified from their original sources.

---

## License

Competition materials are provided for use in the ISQED 2026 Agentic AI Design Verification Challenge only. See individual files for applicable licenses.
