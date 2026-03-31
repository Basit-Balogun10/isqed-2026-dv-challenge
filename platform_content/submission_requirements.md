# Submission Requirements — Per-Task File Specifications

This document defines the **exact files, formats, and naming conventions** required for each task. The automated evaluation pipeline validates these strictly — submissions that do not conform will receive partial or zero credit.

---

## Universal Requirements (All Tasks)

Every submission, regardless of task, **must** include:

| File | Format | Purpose |
|------|--------|---------|
| `metadata.yaml` | YAML | Team ID, task ID, DUT ID, simulator, timestamp |
| `methodology.md` | Markdown | AI usage documentation (see below) |
| `prompts/` or LLM link | Dir or URL | LLM conversation evidence (see below) |
| `Makefile` | GNU Make | Build and run targets |

### metadata.yaml (Required)

```yaml
team_name: "your-team-name"
task_id: "1.1"                    # Must match the task you are submitting for
dut_id: "nexus_uart"              # Omit for tasks that are not per-DUT
simulator: "icarus"               # One of: icarus, verilator, vcs, questa, xcelium
timestamp: "2026-04-01T14:30:00Z" # ISO 8601
```

### methodology.md (Required)

Must contain these sections (use these exact headings):

```markdown
# Methodology

## AI Tools Used
## Prompt Engineering Strategies
## Iteration Process
## Human vs AI Contribution
## Failed Approaches
## Efficiency Metrics
## Reproducibility
```

Submissions missing `methodology.md` receive **0 points** for the AI Integration component (20% of score).

### LLM Conversation Evidence (Required)

Every submission must include verifiable evidence of LLM/agent interactions. Provide **at least one** of:

1. **Shareable conversation link** in `methodology.md` — e.g., ChatGPT share links, Claude.ai shared conversations (preferred)
2. **`prompts/` directory** — Markdown or text files containing your key prompts and the LLM's responses. Include at minimum your 5 most impactful prompts.
3. **`agent_log.json`** — If you built an agentic system, the full execution trace showing LLM calls, prompts, responses, and actions taken.

Submissions with no conversation evidence receive **at most half credit** on AI Integration (20% of total score). You may redact API keys or personal information.

### Makefile (Required)

Must support at minimum:

```makefile
# Path A (cocotb/pyuvm)
compile:        # Compile DUT + testbench
simulate:       # Run all tests
coverage:       # Generate coverage reports
clean:          # Remove build artifacts

# Path B (commercial) — add if applicable
sim_vcs:        # Compile and run with VCS
sim_questa:     # Compile and run with Questa
sim_xcelium:    # Compile and run with Xcelium
```

### Accepted File Types

| Extension | Allowed | Notes |
|-----------|---------|-------|
| `.py` | Yes | cocotb/pyuvm testbench code |
| `.sv`, `.v`, `.svh`, `.vh` | Yes | SystemVerilog/Verilog (testbench only — do not include DUT RTL) |
| `.yaml`, `.yml` | Yes | Configuration, metadata, verification plans |
| `.md` | Yes | Documentation, reports, methodology |
| `.json` | Yes | Structured analysis results, agent logs |
| `.hjson` | Yes | Register maps (if extending) |
| `.html` | Yes | Coverage reports |
| `.txt`, `.log` | Yes | Regression logs, text reports |
| `.vcd`, `.fst` | No | Waveforms are too large — do not include |
| `.pdf` | No | Use markdown instead |
| `.zip`, `.tar.gz` | No | Do not nest archives |

**Maximum submission size: 50 MB.** Submissions exceeding this will be rejected.

---

## Phase 1 — Verification Environment Construction

### Task 1.1: Interface Agent Generation

**Submit per DUT** (up to 3 DUTs scored). One zip per DUT.

```
submission-1.1-{dut_id}/
├── testbench/
│   ├── tl_ul_agent.py            — TL-UL bus driver + monitor (REQUIRED)
│   ├── tl_ul_monitor.py          — TL-UL bus monitor (or combined in agent)
│   ├── tl_ul_sequences.py        — TL-UL read/write/burst sequences
│   ├── protocol_agent.py         — Protocol agent (UART/SPI/I2C/GPIO) if applicable
│   ├── scoreboard.py             — Reference model + transaction comparison (REQUIRED)
│   ├── coverage.py               — Coverage model (REQUIRED)
│   └── env.py                    — Top-level environment wiring it all together (REQUIRED)
├── tests/
│   └── test_basic.py             — At least 1 test that exercises the environment (REQUIRED)
├── methodology.md                — REQUIRED
├── Makefile                      — REQUIRED
└── metadata.yaml                 — REQUIRED
```

**Specific requirements:**
- `scoreboard.py` must contain a reference model class that predicts expected DUT outputs given inputs
- `env.py` must instantiate the agent(s), scoreboard, and coverage collector
- `tests/test_basic.py` must pass on the provided clean RTL with zero assertion failures
- Protocol agents are required for: `nexus_uart` (UART), `bastion_gpio` (GPIO), `citadel_spi` (SPI), `rampart_i2c` (I2C). Not required for `warden_timer`, `aegis_aes`, `sentinel_hmac` (CSR-only interface)
- For Path B (SV UVM): replace `.py` files with `.sv` packages. Structure under `testbench/` with `agents/`, `env/`, `tests/` subdirs containing SV packages

**Automated evaluation checks:**
1. Compiles with reference RTL? (pass/fail)
2. Required files present? (checklist)
3. Tests pass on clean RTL? (pass/fail)
4. Scoreboard reports transaction matches? (pass/fail)

---

### Task 1.2: Verification Plan to Test Suite

**Submit per DUT** (up to 3 DUTs scored). One zip per DUT.

```
submission-1.2-{dut_id}/
├── tests/
│   ├── test_vp_001.py            — One test file per VP item (RECOMMENDED)
│   ├── test_vp_002.py            — Or grouped logically
│   ├── ...
│   └── test_all.py               — Or a single file with all tests (ACCEPTABLE)
├── vplan_mapping.yaml            — Maps VP-IDs to test names and coverage bins (REQUIRED)
├── methodology.md
├── Makefile
└── metadata.yaml
```

**Specific requirements:**
- `vplan_mapping.yaml` must follow this format:
  ```yaml
  mappings:
    - vp_id: "VP-UART-001"
      test_name: "test_vp_001::test_basic_tx_rx"
      coverage_bins: ["cp_baud_div.low", "cp_parity_mode.none"]
    - vp_id: "VP-UART-002"
      test_name: "test_vp_002::test_fifo_full"
      coverage_bins: ["cp_tx_fifo.full"]
  ```
- Every test must use `@cocotb.test()` decorator (Path A) or extend `uvm_test` (Path B)
- Every test must have a docstring referencing the VP-ID it covers
- All tests **must pass on clean RTL**. Tests that fail on clean RTL incur a **-10 point penalty each**

**Automated evaluation checks:**
1. Parse `vplan_mapping.yaml` — is it valid?
2. Do all referenced test functions exist?
3. Run all tests on clean RTL — any failures? (penalty)
4. Run tests with coverage — do the claimed coverage bins get hit?

---

### Task 1.3: Register Verification Suite

**Submit once** (covers all DUTs). Single zip.

```
submission-1.3/
├── generator/
│   ├── csr_test_generator.py     — Script that reads Hjson and generates tests (REQUIRED)
│   └── templates/                — Jinja2 or string templates (if used)
├── generated_tests/
│   ├── test_csr_nexus_uart.py    — Generated test for each DUT (REQUIRED, at least 3 DUTs)
│   ├── test_csr_bastion_gpio.py
│   ├── test_csr_warden_timer.py
│   └── ...
├── methodology.md
├── Makefile                      — Must have target: generate (runs the generator)
└── metadata.yaml
```

**Specific requirements:**
- `generator/csr_test_generator.py` must be a runnable script:
  ```bash
  python generator/csr_test_generator.py --csr-map <path_to_hjson> --output <path_to_test.py>
  ```
- Generated tests must cover per register: **reset value**, **read/write** (for RW fields), **read-only** (for RO fields), **write-1-to-clear** (for W1C fields), **bit isolation** (walking-1/walking-0)
- The generator must work for **any** DUT's Hjson CSR map — not just hardcoded for specific DUTs
- Include generated tests for at least 3 DUTs

**Automated evaluation checks:**
1. Run generator on each DUT's Hjson — does it produce valid Python/SV?
2. Run generated tests per DUT — per-register pass/fail
3. Is the generator truly generic? (run on a hidden Hjson to verify)

---

### Task 1.4: Assertion Library

**Submit per DUT** (up to 2 DUTs scored). One zip per DUT.

```
submission-1.4-{dut_id}/
├── assertions/
│   ├── protocol_assertions.sv    — TL-UL and protocol-level SVA (REQUIRED)
│   ├── functional_assertions.sv  — Behavioral properties from spec (REQUIRED)
│   ├── structural_assertions.sv  — Reset, FSM, one-hot checks
│   └── liveness_assertions.sv    — Eventually/liveness properties
├── bind_file.sv                  — SVA bind module that attaches assertions to DUT (REQUIRED)
├── assertion_manifest.yaml       — Lists all assertions with descriptions (REQUIRED)
├── tests/
│   └── test_with_assertions.py   — Test that exercises assertions (REQUIRED)
├── methodology.md
├── Makefile
└── metadata.yaml
```

**Specific requirements:**
- `assertion_manifest.yaml` format:
  ```yaml
  assertions:
    - name: "tl_ul_handshake_stable"
      file: "protocol_assertions.sv"
      type: "protocol"
      description: "A-channel signals stable while valid and not ready"
      spec_ref: "TL-UL protocol spec, Section 4"
    - name: "uart_tx_idle_high"
      file: "functional_assertions.sv"
      type: "functional"
      description: "TX line must be high when idle and TX enabled"
      spec_ref: "nexus_uart spec, Section 5.2"
  ```
- Minimum **20 assertions** per DUT for full score
- Assertions may be SVA (in `.sv` files with bind) or cocotb-based (in `.py` files using `cocotb.triggers` timing checks)
- Path A teams: SVA assertions are compiled alongside the DUT via the bind file. Your Makefile must include the bind file in compilation
- `tests/test_with_assertions.py` must run a simulation that exercises assertion conditions (both pass and fire paths)

**Automated evaluation checks:**
1. Compile assertions + bind file + DUT — no errors?
2. Run on clean RTL — **zero assertion failures** (required gate)
3. Run on each buggy variant (`-DSEED_BUG_N`) — which assertions fire?
4. Count total assertions from manifest

---

## Phase 2 — Coverage Closure Campaign

### Task 2.1: Coverage Gap Analysis

**Submit once** (all DUTs). Single zip.

```
submission-2.1/
├── gap_analysis/
│   ├── nexus_uart_gaps.md        — Gap analysis per DUT (at least 2 DUTs) (REQUIRED)
│   ├── bastion_gpio_gaps.md
│   └── ...
├── summary.md                    — Executive summary across all analyzed DUTs (REQUIRED)
├── priority_table.yaml           — Prioritized gap list (REQUIRED)
├── methodology.md
└── metadata.yaml
```

**Specific requirements:**
- Each `{dut}_gaps.md` must contain:
  - Table of uncovered code regions (file, line range, reason uncovered)
  - Table of unhit functional coverage bins (coverpoint, bin name, required stimulus)
  - Per-gap: root cause analysis (1-3 sentences) and test intent description
- `priority_table.yaml` format:
  ```yaml
  priorities:
    - rank: 1
      dut: "nexus_uart"
      gap: "RX timeout path never exercised"
      severity: "high"
      difficulty: "medium"
      estimated_coverage_gain: "5-8% line coverage"
      test_intent: "Configure RX, send partial byte, wait for timeout period"
  ```
- Analyze **at least 2 DUTs** for full score

**Automated evaluation checks:**
1. Required files present and parseable?
2. Referenced uncovered regions actually exist in the coverage DB?

**Judge evaluation:** Completeness (100pts), root cause accuracy (50pts), prioritization quality (50pts)

---

### Task 2.2: Stimulus Engineering

**Submit per DUT** (up to 4 DUTs scored). One zip per DUT.

```
submission-2.2-{dut_id}/
├── testbench/                    — Full testbench (may reuse from Task 1.1)
│   └── ...
├── tests/
│   ├── test_reference.py         — Reference testbench tests (INCLUDE THESE) (REQUIRED)
│   ├── test_coverage_*.py        — Your new coverage-closing tests (REQUIRED)
│   └── ...
├── results/
│   ├── coverage_before.txt       — Baseline coverage numbers (REQUIRED)
│   └── coverage_after.txt        — Your improved coverage numbers (REQUIRED)
├── methodology.md
├── Makefile
└── metadata.yaml
```

**Specific requirements:**
- You **must include** the reference testbench tests alongside your new tests. Coverage is measured from the complete suite
- `coverage_before.txt` and `coverage_after.txt` must contain at minimum:
  ```
  line_coverage: 42.3
  branch_coverage: 31.1
  toggle_coverage: 26.8
  functional_coverage: 21.0
  ```
- New test files must be clearly distinguishable from reference tests (use `test_coverage_` prefix)
- Makefile must have `coverage` target that produces Verilator coverage output

**Automated evaluation checks:**
1. Compile and run full test suite with coverage instrumentation
2. Measure line/branch/toggle/FSM/functional coverage
3. Compare against known baseline → compute improvement → score

---

### Task 2.3: Coverage-Directed Test Generation

**Submit once**. Single zip.

```
submission-2.3/
├── cdg_system/
│   ├── cdg_engine.py             — Main CDG engine (REQUIRED)
│   ├── coverage_analyzer.py      — Parses coverage results
│   ├── constraint_tuner.py       — Adjusts constraint distributions
│   └── config.yaml               — CDG parameters
├── tests/
│   ├── test_cdg_generated.py     — Tests generated by the CDG system
│   └── ...
├── results/
│   ├── convergence_log.csv       — Per-iteration: cycle count, coverage achieved (REQUIRED)
│   └── final_coverage.txt        — Final coverage numbers
├── methodology.md
├── Makefile                      — Must have target: run_cdg (executes the full CDG loop)
└── metadata.yaml
```

**Specific requirements:**
- `cdg_engine.py` must be runnable:
  ```bash
  python cdg_system/cdg_engine.py --dut <dut_id> --budget 100000 --output results/
  ```
- `convergence_log.csv` format:
  ```csv
  iteration,cycles_used,line_coverage,branch_coverage,functional_coverage
  1,5000,45.2,33.1,22.0
  2,10000,52.8,39.4,28.5
  ...
  ```
- The system must demonstrate **adaptive behavior** — coverage should improve faster than uniform random baseline
- Target DUT: choose any one DUT to demonstrate on

**Automated evaluation checks:**
1. Run CDG engine with fixed 100k cycle budget
2. Compare coverage achieved vs baseline random at same budget
3. Measure convergence rate (cycles to reach 85%)

---

## Phase 3 — Debug & Root-Cause Analysis

### Task 3.1: The Log Whisperer

**Submit once** (covers all 10 provided failures). Single zip.

```
submission-3.1/
├── analysis/
│   ├── failure_01.yaml           — Analysis per failure (REQUIRED, all 10)
│   ├── failure_02.yaml
│   ├── ...
│   └── failure_10.yaml
├── summary.md                    — Overview of analysis approach
├── preprocessing/                — Any log preprocessing scripts (OPTIONAL)
│   └── log_parser.py
├── methodology.md
└── metadata.yaml
```

**Specific requirements:**
- Each `failure_NN.yaml` must follow this exact format:
  ```yaml
  failure_id: 1
  classification: "functional_bug"    # One of: functional_bug, testbench_bug,
                                      #         protocol_violation, timing_issue,
                                      #         configuration_error
  root_module: "nexus_uart"           # Module name where bug originates
  root_line_range: "245-260"          # Approximate RTL line range
  root_cause: |
    The RX FIFO write pointer wraps incorrectly when the FIFO transitions
    from full to empty in a single cycle due to simultaneous read and write.
    This causes the read pointer to corrupt, losing all buffered data.
  suggested_fix: |
    Add a guard condition to the pointer update logic that prevents
    simultaneous wrap of both read and write pointers in the same cycle.
  confidence: 0.85                    # 0.0 to 1.0
  ```
- All 10 failures must be analyzed. Missing entries receive 0 points for that failure.

**Automated evaluation checks:**
1. All 10 YAML files present and parseable?
2. `classification` matches ground truth? (10 pts each)
3. `root_module` matches ground truth? (10 pts each)

**Judge evaluation:** Root cause description quality (15 pts/failure), fix suggestion (5 pts/failure)

---

### Task 3.2: The Trace Detective

**Submit once** (covers all 5 provided failures). Single zip.

```
submission-3.2/
├── analysis/
│   ├── trace_01.yaml             — Debug trace per failure (REQUIRED, all 5)
│   ├── trace_02.yaml
│   ├── ...
│   └── trace_05.yaml
├── reproduction_tests/
│   ├── repro_01.py               — Minimal reproduction test (REQUIRED, all 5)
│   ├── repro_02.py
│   ├── ...
│   └── repro_05.py
├── methodology.md
├── Makefile                      — Must have target: run_repro (runs all reproduction tests)
└── metadata.yaml
```

**Specific requirements:**
- Each `trace_NN.yaml`:
  ```yaml
  failure_id: 1
  manifestation_cycle: 1547          # Exact clock cycle where bug is visible
  root_cause_cycle: 1483             # Cycle where the root cause occurs
  root_cause_file: "warden_timer.sv"
  root_cause_line: 187
  signal_trace:                      # Dependency chain from symptom → cause
    - cycle: 1547
      signal: "intr_o[0]"
      value: 1
      note: "Spurious timer0 interrupt fires"
    - cycle: 1546
      signal: "timer0_expired"
      value: 1
      note: "Comparator output asserts unexpectedly"
    - cycle: 1545
      signal: "mtime"
      value: "0x0000_0000_0000_FFFF"
      note: "mtime value during comparison"
    - cycle: 1483
      signal: "mtimecmp0_low"
      value: "0x0000_FF00"
      note: "LOW half written, HIGH half still stale — TOCTOU race"
  root_cause_description: |
    Writing MTIMECMP0_LOW triggers an immediate comparison with the stale
    HIGH half, causing a spurious match when the new LOW value happens to
    satisfy the comparison with the old HIGH value.
  ```
- Each `repro_NN.py` must be a standalone cocotb test that triggers **only** the target bug. It should:
  - Complete in under 5000 clock cycles
  - Fail with a clear assertion or scoreboard error message
  - Not require any external dependencies beyond cocotb and the DUT

**Automated evaluation checks:**
1. `manifestation_cycle` within ±2 of ground truth? (15 pts each)
2. Run each `repro_NN.py` against buggy RTL — does it fail? (30 pts each)

**Judge evaluation:** Signal trace quality (30 pts/failure), root cause location (25 pts/failure)

---

### Task 3.3: The Regression Medic

**Submit once**. Single zip.

```
submission-3.3/
├── bucketing.yaml                — Failure-to-bucket mapping (REQUIRED)
├── bug_descriptions.yaml         — Root cause per unique bug (REQUIRED)
├── priority_ranking.yaml         — Bugs ranked by severity (REQUIRED)
├── patch_validation.yaml         — Fix-to-bug mapping + regression results (REQUIRED)
├── analysis_scripts/             — Any scripts used for analysis (OPTIONAL)
│   └── ...
├── methodology.md
└── metadata.yaml
```

**Specific requirements:**
- `bucketing.yaml`:
  ```yaml
  buckets:
    - bucket_id: 1
      description: "FIFO pointer corruption on simultaneous read/write"
      failure_ids: [3, 7, 12, 18, 25]
    - bucket_id: 2
      description: "Interrupt re-fire after W1C clear"
      failure_ids: [1, 5, 9, 14, 22, 31]
    # ... all 35 failures must be assigned to exactly one bucket
  ```
- `bug_descriptions.yaml`:
  ```yaml
  bugs:
    - bucket_id: 1
      root_cause: |
        Detailed root cause description...
      affected_module: "nexus_uart"
      affected_lines: "127-135"
    # ... one entry per bucket
  ```
- `priority_ranking.yaml`:
  ```yaml
  ranking:
    - rank: 1
      bucket_id: 3
      severity: "critical"
      rationale: "Data corruption affects all downstream operations"
    - rank: 2
      bucket_id: 1
      severity: "high"
      rationale: "FIFO corruption causes silent data loss"
    # ... all buckets ranked
  ```
- `patch_validation.yaml`:
  ```yaml
  validations:
    - patch_id: "patch_A"
      fixes_bucket: 2
      introduces_regression: false
      regression_details: null
    - patch_id: "patch_B"
      fixes_bucket: 4
      introduces_regression: true
      regression_details: "Breaks test_037 — new timing violation in SPI hold time"
    # ... one entry per provided patch
  ```

**Automated evaluation checks:**
1. All 35 failures assigned? No duplicates? (structure check)
2. Bucketing accuracy vs ground truth (adjusted Rand index, 100 pts)
3. Patch-to-bug mapping correct? (50 pts)
4. Regression detection correct? (50 pts)

---

## Phase 4 — Agentic Verification Pipeline

### Task 4.1: The AutoVerifier

**Submit once**. Single zip.

```
submission-4.1/
├── agent/
│   ├── run_agent.py              — Agent entry point (REQUIRED)
│   ├── agent_config.yaml         — Agent configuration (REQUIRED)
│   ├── requirements.txt          — Additional Python dependencies (OPTIONAL)
│   └── src/                      — Agent source code
│       └── ...
├── methodology.md
├── Makefile                      — Must have target: run_agent
└── metadata.yaml
```

**Specific requirements:**
- `run_agent.py` must accept this exact CLI interface:
  ```bash
  python agent/run_agent.py \
      --rtl <path_to_dut.sv> \
      --spec <path_to_spec.md> \
      --csr_map <path_to_csr.hjson> \
      --output_dir <path_to_output>
  ```
- The agent must produce this output structure in `output_dir/`:
  ```
  output_dir/
  ├── testbench/          — Generated cocotb/pyuvm or SV UVM environment
  ├── tests/              — Generated test files
  ├── coverage/           — Coverage reports (after running tests)
  ├── assertions/         — Generated assertions
  ├── bug_reports/        — Any bugs found (YAML format)
  ├── report.md           — Verification summary report
  └── agent_log.json      — Full trace of agent actions and LLM calls (REQUIRED)
  ```
- `agent_log.json` must record every LLM API call:
  ```json
  [
    {
      "timestamp": "2026-04-06T10:15:30Z",
      "action": "analyze_rtl",
      "model": "claude-sonnet-4-20250514",
      "prompt_tokens": 4500,
      "completion_tokens": 1200,
      "duration_ms": 3400,
      "summary": "Extracted 12 CSR registers and 3 FSM states from UART RTL"
    }
  ]
  ```
- Agent must complete within **60 minutes** per DUT
- Agent must be **fully autonomous** — no human input after launch
- Participants provide their own LLM API keys via environment variables (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.)

**Automated evaluation (per unseen DUT):**
1. Generated environment compiles? (50 pts)
2. Scoreboard matches transactions? (75 pts)
3. Code coverage achieved (0-100 pts, scaled)
4. Functional coverage achieved (0-100 pts, scaled)
5. Bugs detected on seeded variants (50 pts per bug)
6. False positives on clean RTL (-25 pts each)
7. Completed within 30 min? (+25 bonus)

---

### Task 4.2: The Regression Agent

**Submit once**. Single zip.

```
submission-4.2/
├── agent/
│   ├── run_agent.py              — Agent entry point (REQUIRED)
│   ├── agent_config.yaml
│   ├── requirements.txt
│   └── src/
│       └── ...
├── methodology.md
├── Makefile
└── metadata.yaml
```

**Specific requirements:**
- `run_agent.py` must accept:
  ```bash
  python agent/run_agent.py \
      --commit_stream <path_to_commits.json> \
      --rtl_base <path_to_base_rtl_dir> \
      --test_suite <path_to_test_suite> \
      --output_dir <path_to_output>
  ```
- For each commit in the stream, the agent must output a verdict file in `output_dir/`:
  ```
  output_dir/
  ├── verdicts/
  │   ├── commit_01.json
  │   ├── commit_02.json
  │   └── ...
  └── agent_log.json
  ```
- Each `commit_NN.json`:
  ```json
  {
    "commit_id": "abc123",
    "verdict": "FAIL",
    "confidence": 0.92,
    "tests_run": 15,
    "tests_total": 200,
    "failures": ["test_uart_parity", "test_uart_loopback"],
    "bug_description": "Parity calculation inverted for odd parity mode",
    "affected_module": "nexus_uart",
    "decision_time_seconds": 45
  }
  ```
  - `verdict` must be one of: `PASS`, `FAIL`, `COVERAGE_REGRESSION`

**Automated evaluation:**
- 20 commits evaluated against ground truth verdicts
- Scoring per commit type (see scoring rubric)

---

### Task 4.3: The Spec Interpreter

**Submit once**. Single zip.

```
submission-4.3/
├── agent/
│   ├── run_agent.py              — Agent entry point (REQUIRED)
│   ├── agent_config.yaml
│   ├── requirements.txt
│   └── src/
│       └── ...
├── methodology.md
├── Makefile
└── metadata.yaml
```

**Specific requirements:**
- `run_agent.py` must accept:
  ```bash
  python agent/run_agent.py \
      --spec <path_to_spec.md> \
      --output_dir <path_to_output>
  ```
- The agent must produce in `output_dir/`:
  ```
  output_dir/
  ├── vplan.yaml              — Structured verification plan (REQUIRED)
  ├── test_stubs/             — Cocotb test stubs (REQUIRED)
  │   └── test_*.py
  ├── coverage_model.yaml     — Functional coverage specification (REQUIRED)
  ├── assertions.yaml         — Behavioral property specifications (REQUIRED)
  ├── report.md               — Agent's reasoning and analysis
  └── agent_log.json          — LLM call trace (REQUIRED)
  ```
- `vplan.yaml` format:
  ```yaml
  vplan:
    - id: "VP-001"
      feature: "Basic transmit"
      description: "Verify single byte transmission with default configuration"
      priority: "high"
      coverage_goals: ["tx_data_pattern", "baud_rate_config"]
      test_strategy: "Direct test with known data patterns"
  ```
- `coverage_model.yaml` format:
  ```yaml
  covergroups:
    - name: "basic_operation_cg"
      coverpoints:
        - name: "cp_mode"
          description: "Operating mode"
          bins: ["mode_a", "mode_b", "mode_c"]
      crosses:
        - name: "cx_mode_x_data"
          coverpoints: ["cp_mode", "cp_data_pattern"]
  ```
- `assertions.yaml` format:
  ```yaml
  assertions:
    - name: "req_resp_within_N_cycles"
      type: "liveness"
      property: "Every valid request receives a response within 20 cycles"
      importance: "critical"
  ```

**Automated evaluation:**
1. Output structure valid? Files parseable?
2. YAML syntax correct?
3. Test stubs are valid Python?

**Judge evaluation (80%):** Vplan completeness, accuracy, coverage model quality, assertion quality — each 0-100 pts.

---

## Submission Checklist

Before uploading, verify:

- [ ] `metadata.yaml` has correct `task_id` and `dut_id`
- [ ] `methodology.md` exists with all required sections
- [ ] LLM conversation evidence included (shareable link, `prompts/` dir, or `agent_log.json`)
- [ ] `Makefile` exists with required targets
- [ ] No DUT RTL files included (we provide those)
- [ ] No waveform dumps (`.vcd`, `.fst`, `.vpd`, `.fsdb`)
- [ ] Total zip size under 50 MB
- [ ] Tests pass on clean RTL (Phase 1 & 2 tasks)
- [ ] All YAML files are valid (parse them locally first)
- [ ] File paths in your code use relative paths, not absolute
