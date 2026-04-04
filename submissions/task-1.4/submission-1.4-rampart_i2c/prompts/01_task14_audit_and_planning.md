User: Awesome, no we begin task 1.4. Let's begin as you did with 1.3 (the audit and then the plan)

#file:task_1_4_assertion_library.md #file:submission_requirements.md #file:instructions_and_documentation.md #file:evaluation_rubrics.md #file:competition_rules.md 

GitHub Copilot: You want a Task 1.4 kickoff exactly like Task 1.3: first a concrete audit of what already exists, then a structured execution plan. I’ll start by inventorying all current Task 1.4 artifacts and helper scripts so the plan is grounded in the real repository state, not assumptions.Optimizing tool selection...

Searched for files matching `**/submissions/task-1.4/**`, no matches

Searched for files matching `**/scripts/**/*1.4*`, no matches

Searched for files matching `**/*assert*{.py,.sv,.svh,.md,.yaml,.yml,.csv}`, 1 match

Read memory

Quick audit result so far: there is currently no Task 1.4 submission directory and no Task 1.4 helper scripts yet, so we’ll likely need to bootstrap both from existing Task 1.3 patterns. Next I’m checking Task 1.3/1.2 structures and memory notes to extract the exact template we should clone.

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.3)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/scripts)

Read memory [](file:///home/abdulbasit/.vscode-server/data/User/workspaceStorage/c30b0291fa9be6a8af4be3b016c4d21c/GitHub.copilot-chat/memory-tool/memories/repo/task_1_3_lessons.md)

Created 4 todos

I have enough baseline context to start the real audit now: I’m pulling exact Task 1.4 requirements plus what we already built in Tasks 1.1/1.2 that can be reused for top-tier DUTs. This will directly drive a practical, no-guesswork plan.

Ran terminal command:  cd /home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge && rg --files | rg -i 'assert|bind|manifest|task-1\.4|submission-1\.4'
Completed with input:  cd /home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge && rg --files | rg -i 'assert|bind|manifest|task-1\.4|submission-1\.4'

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.1)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/platform_content/submission_requirements.md#180-180), lines 180 to 340

Small blocker found: this environment doesn’t have ripgrep installed, so I’m switching to built-in workspace search tools and continuing the audit. Next I’ll inspect reusable 1.2 DUT environments and check whether any assertion scaffolding already exists.

Searched for files matching `**/*assert*.sv`, no matches

Searched for files matching `**/*assert*.py`, no matches

Searched for files matching `**/bind*.sv`, no matches

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-rampart_i2c)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-sentinel_hmac)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-aegis_aes)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-rampart_i2c/testbench)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-rampart_i2c/tests)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-sentinel_hmac/testbench)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-sentinel_hmac/tests)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-aegis_aes/testbench)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-aegis_aes/tests)

Audit update: we have strong reusable test infrastructure for the three high-value DUTs from Task 1.2, and currently zero existing assertion/bind assets, so Task 1.4 starts from a clean assertion codebase. I’m now checking Makefile conventions and DUT top-level ports/internal structure to pick the best two DUTs and shape the plan.

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-rampart_i2c/Makefile)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-sentinel_hmac/Makefile)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-aegis_aes/Makefile)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/sentinel_hmac/sentinel_hmac.sv#1-1), lines 1 to 260

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/aegis_aes/aegis_aes.sv#1-1), lines 1 to 260

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/rampart_i2c/rampart_i2c.sv#1-1), lines 1 to 260

Starting: *Audit reusable assertion assets* (2/4)

Searched for regex `typedef enum|state|busy|done|intr|fifo|alert_o|assign intr_o` (`**/duts/rampart_i2c/rampart_i2c.sv`), 200 results

Searched for regex `typedef enum|state|busy|done|intr|fifo|alert_o|assign intr_o` (`**/duts/sentinel_hmac/sentinel_hmac.sv`), 186 results

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-rampart_i2c/tests/helpers.py)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-sentinel_hmac/tests/helpers.py)

I’ve confirmed the internal signal richness for both rampart_i2c and sentinel_hmac, which is excellent for high-value functional/structural/liveness SVAs. I’m now checking the existing submission automation scripts so our Task 1.4 plan includes the same package-first readiness workflow you liked in 1.3.

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/scripts/verify-readiness.sh)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/scripts/manage-1.3-submissions.sh)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/scripts/verify-1.3-readiness.sh)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/scripts/regenerate_prompt_evidence.sh)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/scripts/manage-1.1-submissions.sh)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/scripts/verify-1.1-readiness.sh)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/README.md)

Core automation finding: readiness tooling currently exists only for 1.1–1.3, so for 1.4 we’ll need a new per-DUT packaging and ZIP-first verifier script family modeled on 1.1. I’m taking one final pass on scoring and simulator constraints to lock the DUT selection and milestone plan.

Searched for regex `Known Simulator Notes|aegis_aes|Compilation check|both Verilator and Icarus|Task 1.4` (`**/platform_content/instructions_and_documentation.md`), 9 results

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/platform_content/evaluation/evaluation_rubrics.md#110-110), lines 110 to 220

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/platform_content/competition_rules.md#120-120), lines 120 to 214

Searched for regex `Task 1.4|Assertion Library|Per bug caught|Assertion count` (`**/platform_content/evaluation/evaluation_rubrics.md`), 4 results

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/platform_content/evaluation/evaluation_rubrics.md#92-92), lines 92 to 130

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/platform_content/instructions_and_documentation.md#744-744), lines 744 to 766

I now have enough evidence to lock strategy: for Task 1.4 the best risk-adjusted pair is rampart_i2c plus sentinel_hmac, because both work on Icarus and Verilator while aegis_aes has an Icarus simulation hang caveat. I’ll capture one repository memory note from this audit, then I’ll present the full audit report and execution plan.

Inserted into memory file [](file:///home/abdulbasit/.vscode-server/data/User/workspaceStorage/c30b0291fa9be6a8af4be3b016c4d21c/GitHub.copilot-chat/memory-tool/memories/repo/task_1_3_lessons.md)

Starting: *Draft Task 1.4 execution plan* (4/4)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/platform_content/tasks/task_1_4_assertion_library.md#180-180), lines 180 to 280

Completed: *Draft Task 1.4 execution plan* (4/4)

**Task 1.4 Audit Complete**

1. Requirements baseline is clear and strict.
- Task definition and assertion philosophy are in task_1_4_assertion_library.md.
- Evaluator hard gates are in evaluation_rubrics.md: clean RTL must have zero false fires, and assertion count must be at least 20 per DUT.
- Submission structure rules are in submission_requirements.md: per-DUT zip, required assertion files, bind file, manifest, and test entrypoint.

2. Current repository status for Task 1.4.
- No existing Task 1.4 submission directories were found under submissions.
- No existing assertion source or bind files were found in the workspace.
- Existing readiness automation currently covers 1.1 to 1.3 only, based on verify-readiness.sh, verify-1.1-readiness.sh, and verify-1.3-readiness.sh.
- Strong reusable cocotb/TL-UL infrastructure is available from Task 1.2 submissions, especially for top-scoring DUTs in submission-1.2-rampart_i2c and submission-1.2-sentinel_hmac.

3. DUT selection recommendation.
- Primary pair: rampart_i2c + sentinel_hmac.
- Why: highest scoring multipliers with lower simulator risk than aegis_aes, and both are explicitly listed as working on Icarus and Verilator in instructions_and_documentation.md.
- Risk avoided: aegis_aes has documented Icarus simulation hang behavior in instructions_and_documentation.md.

4. Important format ambiguity found.
- Task doc expects docs/assertion_manifest.csv style in task_1_4_assertion_library.md.
- Submission requirements expect assertion_manifest.yaml and bind_file.sv style in submission_requirements.md.
- Plan: satisfy both formats in each DUT submission to de-risk evaluator and judge interpretation.

**Execution Plan (Modeled After Task 1.3)**

1. Scaffold per-DUT submissions.
- Create submission-1.4-rampart_i2c and submission-1.4-sentinel_hmac with required folder skeleton.
- Add prompts evidence directory from transcript chunking approach used in Task 1.3.

2. Build assertion architecture.
- Protocol assertions: TL-UL handshake/stability/response properties.
- Functional assertions: spec-driven behavior properties tied to register commands and expected outcomes.
- Structural assertions: invariants on control-path and data-path internals.
- Liveness assertions: bounded forward-progress properties to avoid deadlock hangs in simulation.
- Concept note:
Data path means where payload information moves/transforms (FIFO contents, digest words, data bytes).
Control path means how sequencing/decisions happen (FSM states, enable bits, command acceptance).
A FIFO is a queue with ordering and occupancy invariants that are ideal assertion targets.

3. Bind strategy.
- Use bind modules to attach assertions without editing DUT RTL.
