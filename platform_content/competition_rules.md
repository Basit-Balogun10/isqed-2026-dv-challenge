# Competition Rules

## Agentic AI Design Verification Challenge 2026 — ISQED 2026

---

## 1. Competition Overview

The Agentic AI Design Verification Challenge 2026 is a week-long competition hosted at the 27th International Symposium on Quality Electronic Design (ISQED 2026). Teams will apply AI-assisted methodologies to verify RTL designs of increasing complexity, demonstrating mastery of modern verification workflows, coverage-driven techniques, and agentic AI pipelines.

This is a **Design Verification** competition. The goal is to build robust verification environments, achieve coverage closure, debug failing designs, and construct autonomous verification agents — not to find security vulnerabilities. Participants are evaluated on the quality of their verification methodology and how effectively they leverage AI tools throughout the process.

**What is at stake:** Top-performing teams will be recognized with awards across seven categories, and results will be presented at the ISQED 2026 conference. This is an opportunity to showcase cutting-edge verification skills to both academic and industry audiences.

---

## 2. Eligibility

- The competition is **open to all registered teams**, including university and industry participants.
- Each team must have **1 to 4 members**.
- All team members must be registered on the competition platform before the start of the competition.
- A participant may belong to only one team.

---

## 3. Competition Timeline

The competition runs from **March 31 through April 7, 2026** (one week). It is divided into four phases. Phases overlap slightly — participants may begin Phase N+1 while finishing Phase N.

| Phase | Title | Window | Duration |
|-------|-------|--------|----------|
| **Phase 1** | Verification Environment Construction | Days 1–3 (Mar 31 – Apr 2) | 72 hours |
| **Phase 2** | Coverage Closure Campaign | Days 3–5 (Apr 2 – Apr 4) | 48 hours |
| **Phase 3** | Debug & Root-Cause Analysis | Days 5–6 (Apr 4 – Apr 5) | 36 hours |
| **Phase 4** | Agentic Verification Pipeline | Days 6–7 (Apr 5 – Apr 7) | 36 hours |

### Phase Descriptions

**Phase 1 — Verification Environment Construction (72 hrs)**
Build testbenches, define stimulus generators, set up coverage models, and establish a working simulation environment for the provided DUTs.

**Phase 2 — Coverage Closure Campaign (48 hrs)**
Drive functional and code coverage to closure. Develop constrained-random tests, write directed tests for hard-to-reach coverage points, and refine stimulus strategies.

**Phase 3 — Debug & Root-Cause Analysis (36 hrs)**
Identify, isolate, and document bugs injected into the RTL designs. Provide root-cause analysis and, where applicable, propose fixes.

**Phase 4 — Agentic Verification Pipeline (36 hrs)**
Design and deploy an autonomous AI-driven verification agent that can generate tests, analyze coverage, triage failures, and iterate — with minimal human intervention.

---

## 4. Submission Rules

1. **Multiple submissions per task are allowed.** Only the **highest-scoring submission** per task per DUT will count toward a team's final score.
2. Submissions are **collected and evaluated periodically** on the organizer's infrastructure. Evaluation is not instantaneous; results will appear on the leaderboard after each evaluation cycle.
3. All evaluation is **run on the organizer's server**. Submissions must be self-contained and must not depend on external services at evaluation time (with the exception of Phase 4 agent submissions, which may reference LLM APIs).
4. Each submission must include a **`methodology.md`** file describing:
   - Which AI tools were used and how
   - The verification strategy and rationale
   - Any notable design decisions or trade-offs
5. **Submission format:** A single `.zip` file uploaded via the competition platform. The archive must follow the directory structure specified in the task description for each phase.
6. Late submissions (after a phase's window closes) will not be accepted.

---

## 5. Toolchain Requirements

The competition supports **two verification paths**. Teams may choose either path (or mix them across DUTs). Both are fully supported by the evaluation pipeline.

### Path A — Python-Based Verification (Open-Source)

| Category | Tool | Minimum Version |
|----------|------|-----------------|
| RTL Simulation | Verilator | 5.x |
| RTL Simulation | Icarus Verilog | 12+ |
| Testbench Framework | cocotb | 1.9+ |
| UVM Methodology | pyuvm | 3.0+ |
| Functional Coverage | cocotb-coverage | latest |
| Formal Verification | SymbiYosys | latest stable |
| Language Runtime | Python | 3.11+ |

This is the **recommended path for most teams**. Skeleton environments and reference testbenches are provided in cocotb. Participants are responsible for setting up their own tool environment. Teams without local EDA tools may use free platforms such as [EDA Playground](https://www.edaplayground.com/) which provides access to commercial simulators including VCS and Riviera-PRO.

### Path B — SystemVerilog UVM (Commercial Simulators)

| Category | Tool | Supported Versions |
|----------|------|--------------------|
| RTL Simulation | Synopsys VCS | 2023.x or later |
| RTL Simulation | Siemens Questa / QuestaSim | 2023.x or later |
| RTL Simulation | Cadence Xcelium | 23.x or later |
| UVM Library | IEEE 1800.2 UVM | 1.2 or 2.0 |
| Language | SystemVerilog | IEEE 1800-2017 |

Teams with access to commercial EDA licenses may build full SystemVerilog UVM environments. This path enables:
- Native SystemVerilog constrained-random (`rand`, `constraint`, `randomize()`)
- Full UVM class library (agents, sequences, factory, config_db, TLM ports)
- SystemVerilog Assertions (SVA) with full temporal operator support
- SystemVerilog functional coverage (`covergroup`, `coverpoint`, `cross`)
- Advanced debug features (transaction recording, waveform databases)

**Important for Path B teams:**
- You must include a `Makefile` with both a commercial target (`make sim SIM=vcs` or `make sim SIM=questa`) and an open-source fallback (`make sim SIM=verilator`). The evaluation pipeline will attempt the commercial simulator first; if unavailable, it falls back to the open-source path.
- If your submission uses SystemVerilog UVM features that cannot compile on Verilator/Icarus, provide a `cocotb_wrapper/` directory with a minimal cocotb adapter that exercises the same tests. This ensures your submission can be evaluated even if the commercial tool is temporarily unavailable.
- Your `metadata.yaml` must specify the simulator: `simulator: "vcs"`, `simulator: "questa"`, or `simulator: "verilator"`.

### Mixing Paths

Teams may use Path A for some DUTs and Path B for others. Each submission's `metadata.yaml` declares which simulator it targets. The evaluation pipeline routes accordingly.

### AI Tool Policy

- Participants **may use any AI or LLM tools** of their choosing — including large language models, code generation assistants, agentic frameworks, and custom pipelines.
- All AI tool usage **must be documented** in the `methodology.md` file included with each submission.
- For **Phase 4** (Agentic Verification Pipeline), agents may call any LLM API. **Participants must provide their own API keys**; the competition does not supply API access.

---

## 6. Scoring

### Evaluation Pillars

Team scores are determined across four equally weighted pillars:

| Pillar | Weight | Evaluation Method |
|--------|--------|-------------------|
| **Correctness** | 30% | Automated — compilation, simulation pass/fail, bug detection accuracy |
| **Coverage** | 30% | Automated — code coverage and functional coverage metrics |
| **Methodology** | 20% | Judge panel — quality of verification strategy, documentation, and `methodology.md` |
| **AI Integration** | 20% | Judge panel — effectiveness and innovation in AI tool usage |

### DUT Difficulty Multipliers

Each Design Under Test (DUT) is assigned a difficulty tier. The raw score for a DUT is multiplied by its tier factor:

| Tier | Multiplier | Description |
|------|------------|-------------|
| Tier 1 | 1.0x | Introductory complexity |
| Tier 2 | 1.5x | Moderate complexity |
| Tier 3 | 2.0x | Advanced complexity |
| Tier 4 | 2.5x | Expert-level complexity |

---

## 7. AI Usage Policy

The Agentic AI Design Verification Challenge is designed to evaluate **how effectively teams leverage AI** — not whether they use it. AI usage is expected and encouraged.

1. Teams may use **any AI tools**, including but not limited to: large language models, code generation tools, autonomous agents, retrieval-augmented generation systems, and custom AI pipelines.
2. **All AI usage must be documented** in the `methodology.md` file. This includes which tools were used, what prompts or strategies were employed, and how AI output was validated or refined.
3. **Independent AI-generated solutions are permitted.** Two teams may arrive at similar solutions through independent use of AI tools; this is acceptable and expected.
4. **Plagiarism from other teams is strictly prohibited.** Copying another team's submissions, prompts, strategies, or code — whether directly or through intermediaries — will result in disqualification.
5. **Teams must not share solutions, prompts, or strategies** with other teams during the competition period (March 31 – April 7, 2026).

---

## 8. Code of Conduct

All participants must adhere to the following rules:

1. **No unauthorized access.** Do not attempt to access, view, or obtain other teams' submissions, code, or strategies by any means.
2. **No reverse engineering.** Do not attempt to reverse-engineer, probe, or exploit the evaluation system, leaderboard, or competition infrastructure.
3. **No malicious code.** Submissions must not contain malware, exploit code, fork bombs, excessive resource consumption, or any code designed to disrupt the evaluation environment.
4. **Respect for competition materials.** RTL designs and other materials provided by the organizers are for use solely within this competition.

### RTL Design Disclaimer

> **The RTL designs provided in this competition are modified versions of open-source IP blocks, created exclusively for this competition. They are not production-quality, not security-reviewed, and must not be used outside of this competition context.**

Violations of the Code of Conduct may result in warnings, score penalties, or disqualification at the organizers' sole discretion.

---

## 9. Evaluation Process

### Automated Evaluation

Submissions are **downloaded and evaluated periodically** on organizer-managed infrastructure. The automated evaluation pipeline performs the following steps:

1. **Compilation** — The submission is compiled against the target DUT using the supported toolchain.
2. **Simulation** — Testbenches are executed, and pass/fail results are recorded.
3. **Coverage Measurement** — Code coverage (line, branch, toggle) and functional coverage metrics are extracted.
4. **Bug Detection** — For phases involving debug tasks, the accuracy and completeness of identified bugs are assessed.

Results from automated evaluation are posted to the **leaderboard** after each evaluation cycle.

### Judge Evaluation

A panel of judges reviews submissions for:

- **Code quality** — Readability, structure, and adherence to verification best practices.
- **Methodology** — Depth and clarity of the verification strategy documented in `methodology.md`.
- **AI innovation** — Creativity and effectiveness in applying AI tools to verification challenges.

### Final Results

Final standings incorporate **both automated scores and judge panel scores** according to the pillar weights defined in Section 6. Final results are announced after the last evaluation cycle and judge review are complete.

---

## 10. Dispute Resolution

- If a team believes a scoring error or policy violation has occurred, they should contact the organizers through the competition platform's official communication channel.
- Disputes must be raised **within 24 hours** of the relevant score being posted.
- The organizers will review the dispute and respond within a reasonable timeframe.
- **All decisions by the organizers and the judge panel are final and binding.** There is no appeals process beyond the initial dispute review.
- Judge scores for methodology, AI integration, and code quality are qualitative assessments. These scores reflect the professional judgment of the evaluation panel and are not subject to challenge on the basis of differing opinion.
- Automated scores are computed deterministically from the evaluation pipeline. Disputes regarding automated scores will only be considered if there is evidence of a pipeline malfunction (e.g., compilation environment error), not disagreements with the scoring formula.

---

*Agentic AI Design Verification Challenge 2026 — ISQED 2026*
*Rules version 1.0 — Published March 2026*
