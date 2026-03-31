# Task 4.1: The AutoVerifier

**Phase 4 | 800 points | Highest-Value Task in the Competition**

---

## Overview

Build a fully autonomous AI agent that, given only RTL source code, a natural-language specification, and a CSR register map, produces a **complete verification environment from scratch** -- then runs it, measures coverage, and reports bugs. No human intervention. No pre-built templates tuned to a specific DUT. Your agent must generalize.

This is the capstone challenge. It tests the full stack of agentic AI capabilities: code comprehension, verification planning, environment generation, stimulus creation, result analysis, and iterative refinement. The two DUTs used for evaluation will be **unseen** -- they are not among the seven competition DUTs, but they are of comparable complexity and share the same TileLink-UL bus interface.

---

## What Your Agent Must Do

The agent operates in a closed loop through seven stages. Each stage feeds the next.

### Stage 1: ANALYZE

Parse the RTL source to extract:

- Module hierarchy and port list (names, widths, directions)
- Interface identification (TL-UL bus, protocol-specific I/O, interrupts, alerts)
- Finite state machines (states, transitions, encoding)
- Clock domains and reset topology
- CSR address map (cross-referenced against the provided Hjson register map)

### Stage 2: PLAN

Generate a structured verification plan covering:

- Feature list derived from the specification
- Coverage goals (functional bins, code coverage targets)
- Test scenarios (directed, constrained-random, corner cases)
- Prioritized risk areas (complex FSM paths, error handling, boundary conditions)

### Stage 3: BUILD

Produce a working verification environment using **cocotb** or **pyuvm** containing:

- **Bus agent** for TileLink-UL (driver, monitor, transaction model)
- **Protocol agent** for the DUT's external interface (if applicable)
- **Reference model** that predicts expected DUT outputs from input stimulus
- **Scoreboard** that compares DUT outputs against the reference model
- **Functional coverage** collectors aligned with the verification plan

### Stage 4: TEST

Generate and execute test sequences:

- Directed tests targeting specific features from the verification plan
- Constrained-random sequences for broad coverage
- Corner-case and error-injection tests
- CSR access tests (reset values, read/write behavior, access types)

### Stage 5: MEASURE

Collect and analyze coverage results:

- Code coverage (line, branch, toggle, FSM state/transition)
- Functional coverage (bin hit counts vs. plan targets)
- Assertion pass/fail summary

### Stage 6: ITERATE

Analyze coverage gaps and test failures, then autonomously:

- Generate additional stimulus targeting uncovered regions
- Adjust constraint distributions to bias toward coverage holes
- Re-run and re-measure until the time budget is exhausted or targets are met

### Stage 7: REPORT

Produce a structured verification summary including:

- DUT analysis findings (architecture, interfaces, FSMs identified)
- Verification plan (features, coverage goals)
- Test results (pass/fail counts, failure details)
- Coverage achieved (with breakdown by category)
- Bugs found (with reproduction steps and severity assessment)
- Agent methodology (approach taken, iterations performed, LLM usage statistics)

---

## Entry Point

Your agent must be invocable with a single command:

```bash
python run_agent.py \
  --rtl <path_to_rtl_directory> \
  --spec <path_to_spec.md> \
  --csr_map <path_to_csr.hjson> \
  --output_dir <path_to_output_directory>
```

**Arguments:**

| Flag | Description |
|------|-------------|
| `--rtl` | Directory containing all RTL source files (`.sv`, `.v`) for the DUT |
| `--spec` | Path to the natural-language specification (Markdown) |
| `--csr_map` | Path to the Hjson register map file |
| `--output_dir` | Directory where all generated artifacts must be written |

The agent must complete its work within **60 minutes per DUT**, fully autonomously. No interactive prompts, no human-in-the-loop decisions. The timer starts when `run_agent.py` is invoked and ends when the process exits.

---

## Required Output Structure

Upon completion, the output directory must contain the following:

```
output_dir/
├── testbench/          — Generated verification environment
│   ├── agents/         — Bus and protocol agents
│   ├── ref_model/      — Behavioral reference model
│   ├── scoreboard/     — Scoreboard with comparison logic
│   └── coverage/       — Coverage collector definitions
├── tests/              — Generated test files (cocotb/pyuvm)
│   ├── directed/       — Directed test sequences
│   └── random/         — Constrained-random sequences
├── coverage/           — Coverage reports from test execution
│   ├── code_coverage/  — Line, branch, toggle, FSM reports
│   └── func_coverage/  — Functional coverage results
├── assertions/         — Generated SVA or Python-based assertions
├── bug_reports/        — Identified issues (one file per bug)
│   └── bug_001.md      — Bug description, reproduction, severity
├── report.md           — Verification summary (see Stage 7)
└── agent_log.json      — Full trace of agent actions and LLM calls
```

### Agent Log Format

The `agent_log.json` file must record every significant action the agent takes. This is used for both evaluation and reproducibility analysis.

```json
{
  "metadata": {
    "agent_name": "team_example_autoverifier",
    "start_time": "2026-04-06T14:00:00Z",
    "end_time": "2026-04-06T14:47:23Z",
    "total_duration_seconds": 2843,
    "llm_provider": "openai",
    "llm_model": "gpt-4o",
    "total_llm_calls": 142,
    "total_tokens_used": 1284000,
    "estimated_cost_usd": 8.42
  },
  "actions": [
    {
      "step": 1,
      "stage": "ANALYZE",
      "action": "parse_rtl_ports",
      "timestamp": "2026-04-06T14:00:03Z",
      "duration_seconds": 2.1,
      "input_summary": "Parsed 3 RTL files, 1247 lines total",
      "output_summary": "Extracted 24 ports, identified TL-UL interface and SPI signals",
      "llm_call": true,
      "tokens_used": 8200
    },
    {
      "step": 2,
      "stage": "ANALYZE",
      "action": "identify_fsms",
      "timestamp": "2026-04-06T14:00:12Z",
      "duration_seconds": 5.4,
      "input_summary": "FSM extraction from RTL case/always blocks",
      "output_summary": "Found 3 FSMs: tx_fsm (6 states), rx_fsm (5 states), ctrl_fsm (4 states)",
      "llm_call": true,
      "tokens_used": 12400
    }
  ]
}
```

---

## LLM Usage Policy

- Teams may use **any LLM API** (OpenAI, Anthropic, Google, Mistral, open-source, self-hosted, etc.)
- Teams must provide their own API keys; the platform does not supply LLM access
- The agent log must record all LLM calls, including token counts and estimated cost
- There is no cost cap, but **efficiency is evaluated** -- agents that achieve comparable results with fewer LLM calls and lower cost will score higher on the innovation rubric
- Local/open-source models are permitted and encouraged; offline operation is a valid strategy

---

## Evaluation DUTs

Your agent will be evaluated on **2 unseen DUTs** that are revealed only at evaluation time. These DUTs:

- Share the TileLink-UL bus interface used by all competition DUTs
- Have complexity comparable to Tier 2-3 DUTs (600--1200 lines of RTL)
- Include a complete specification document and Hjson register map
- May or may not have an external protocol interface (your agent must handle both cases)
- Contain **seeded bugs** (between 2 and 5 per DUT) for your agent to discover

The evaluation DUTs are designed to test generalizability. Agents that are hard-coded or overfitted to the 7 competition DUTs will perform poorly.

---

## Example Agent Architecture

The following is a reference architecture. You are free to deviate entirely.

```
┌─────────────────────────────────────────────────────┐
│                    Orchestrator                      │
│  (manages pipeline, tracks state, enforces budget)   │
├──────────┬──────────┬───────────┬───────────────────┤
│ Analyzer │ Planner  │ Generator │    Runner         │
│          │          │           │                   │
│ - RTL    │ - VPlan  │ - Env     │ - Sim exec        │
│   parser │   synth  │   builder │ - Coverage        │
│ - Port   │ - Risk   │ - Test    │   collection      │
│   extrac │   assess │   writer  │ - Result          │
│ - FSM    │ - Cover  │ - Assert  │   parsing         │
│   detect │   goals  │   gen     │                   │
├──────────┴──────────┴───────────┴───────────────────┤
│                  Feedback Loop                       │
│  (coverage gap analysis → targeted stimulus gen)     │
└─────────────────────────────────────────────────────┘
```

Key design considerations:

1. **Error recovery**: The agent must handle compilation failures, simulation crashes, and unexpected DUT behavior gracefully. Robust agents retry with corrected code rather than halting.

2. **Time management**: With a 60-minute budget, the agent must allocate time wisely across stages. A common strategy: spend no more than 10 minutes on analysis/planning, 20 minutes on initial build, and reserve 30 minutes for test-iterate-measure cycles.

3. **Incremental building**: Start with a minimal environment that compiles and runs, then layer in complexity. An agent that produces a perfect plan but never compiles anything scores zero on automated metrics.

4. **Reference model strategy**: The reference model is the hardest component to generate correctly. Consider starting with a CSR-register-only model (verifying read/write behavior) and extending to protocol-level modeling only if time permits.

---

## Submission Format

```
submission/
  task_4_1/
    run_agent.py            — Entry point (must accept the CLI args above)
    requirements.txt        — Python dependencies
    agent/                  — Your agent source code
    config/                 — Agent configuration files (if any)
    README.md               — Setup instructions, architecture overview
```

The platform will execute your agent in a sandboxed environment with:

- Python 3.11+
- cocotb 1.9+, pyuvm latest
- Icarus Verilog 12+ and Verilator 5.x
- Network access (for LLM API calls only)
- 16 GB RAM, 8 CPU cores
- 60-minute wall-clock timeout per DUT

---

## Evaluation Rubric

### Automated Scoring (70% -- 560 points)

Evaluated independently on each of the 2 unseen DUTs. Scores are summed across both DUTs.

| Category | Points (per DUT) | Criteria |
|----------|-----------------|----------|
| **Environment Compiles** | 50 pts | Generated testbench compiles without errors against the evaluation DUT RTL. Partial credit (25 pts) if compilation succeeds with warnings only. |
| **Scoreboard Functional** | 75 pts | Scoreboard correctly processes transactions: instantiates, connects to DUT signals, receives and compares at least 10 transactions without crashing. Partial credit (40 pts) for scoreboard that instantiates but has comparison errors. |
| **Code Coverage** | 0--100 pts | Scaled linearly. Line coverage percentage mapped to 0--40 pts. Branch coverage mapped to 0--35 pts. Toggle coverage mapped to 0--25 pts. |
| **Functional Coverage** | 0--100 pts | Scaled based on number of meaningful functional coverage bins defined and hit. Empty or trivial coverage models score 0. Bins must correspond to real DUT features. |
| **Bugs Detected** | 50 pts / bug | Each seeded bug correctly identified and reported with accurate description. Bug report must include: what is wrong, where in the RTL, how to reproduce. |
| **False Positives** | -25 pts each | Each reported bug that does not correspond to an actual defect. Encourages precision over recall. |
| **Time Bonus** | 25 pts | Awarded if the agent completes all stages (including at least one iteration cycle) in under 30 minutes. |

### Judge Scoring (30% -- 240 points)

| Category | Points | Criteria |
|----------|--------|----------|
| **Agent Architecture Innovation** | 0--50 pts | Sophistication of the multi-stage pipeline. Quality of the feedback loop. Error recovery mechanisms. Novel techniques (e.g., RAG over RTL, tree-of-thought planning, formal-method integration). |
| **Generalizability** | 0--25 pts | Evidence that the agent is truly general-purpose and not hard-coded to specific DUT patterns. Evaluated by reviewing agent source code and comparing performance across the two evaluation DUTs. |
| **Efficiency** | 0--50 pts | LLM calls per DUT, total token usage, estimated cost. Agents that achieve strong results with fewer resources score higher. Use of caching, structured prompting, and local processing rewarded. |
| **Report Quality** | 0--25 pts | Clarity, completeness, and accuracy of the generated `report.md`. Must be useful to a verification engineer receiving the report. |
| **Agent Log Quality** | 0--15 pts | Completeness and structure of `agent_log.json`. Enables reproducibility and post-mortem analysis of agent behavior. |
| **Code Quality** | 0--75 pts | Quality of the generated verification environment code. Clean structure, meaningful naming, proper cocotb/pyuvm patterns, useful comments. Evaluated across both DUTs. |

---

## Tips for Success

1. **Build a robust RTL parser first.** Your agent's entire downstream performance depends on correctly understanding the DUT's ports, interfaces, and structure. Invest heavily in the ANALYZE stage.

2. **Compile early, compile often.** An agent that generates beautiful code that never compiles scores zero on automated metrics. Build in a compile-check loop after every generation step.

3. **Start with CSR verification.** Every DUT has a CSR register map. Generating CSR read/write tests from the Hjson file is the most reliable path to early coverage and a working scoreboard.

4. **Plan your time budget explicitly.** Hard-code stage time limits in your orchestrator. An agent that spends 55 minutes planning and 5 minutes building will underperform one that spends 10 minutes planning and 50 minutes in the build-test-iterate loop.

5. **Log everything.** The agent log is not just for scoring -- it is your debugging tool during development. When your agent produces bad output, the log tells you which stage went wrong and what the LLM was thinking.

6. **Test your agent on the competition DUTs first.** While the evaluation uses unseen DUTs, the 7 competition DUTs are your development testbed. If your agent cannot handle `nexus_uart` end-to-end, it will not handle an unseen DUT.

7. **Handle the no-protocol-agent case.** Some DUTs (like `aegis_aes`) interact entirely through CSR registers with no external protocol interface. Your agent must detect this and adapt its environment accordingly.
