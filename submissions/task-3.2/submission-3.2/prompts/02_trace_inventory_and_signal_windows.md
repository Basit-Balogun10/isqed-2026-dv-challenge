
I’m also pulling Task 2.2 lessons for simulator strategy and artifact hygiene, since Task 3.2 still benefits from dual-simulator compile discipline and clean package checks.

Read memory [](file:///home/abdulbasit/.vscode-server/data/User/workspaceStorage/c30b0291fa9be6a8af4be3b016c4d21c/GitHub.copilot-chat/memory-tool/memories/repo/task_2_2_lessons.md)

The gap matrix is complete and I’ve isolated the key schema conflict (`trace_XX/repro_XX` vs richer task-doc naming) plus the missing automation/scripts. I’m now drafting the execution plan with explicit checkpoints, scoring priorities, and validation commands so we can move straight into implementation after your confirmation.

Starting: *Create execution plan and checkpoints* (4/4)

Completed: *Create execution plan and checkpoints* (4/4)

**Task 3.2 Audit Complete**

I audited Task 3.2 requirements and current workspace state against the official hierarchy you referenced.

1. Primary requirement sources used:
1. README.md
2. instructions_and_documentation.md
3. evaluation_rubrics.md
4. task_3_2_trace_detective.md
5. competition_rules.md
6. submission_requirements.md

2. Concept alignment for this task:
1. Manifestation cycle: the clock cycle where the failure is visible (software analogy: where exception surfaces).
2. Root-cause cycle: the earlier cycle where behavior first diverges (software analogy: first corrupt write).
3. Data path: payload movement path (bytes/words through registers, FIFOs, shifters).
4. Control path: decision logic path (FSM state, enables, pointers, counters).
5. FIFO: hardware queue; most bugs are pointer/control bugs, not storage bugs.
6. Trace debugging strategy: backward temporal causality chain from symptom to cause across cycles and hierarchy.

3. What the evaluator will reward most:
1. Automated points: cycle accuracy and repro behavior on buggy RTL per evaluation_rubrics.md.
2. Judge points: high-quality signal dependency chain and precise RTL location/mechanism per task_3_2_trace_detective.md.

---

**Workspace Reality Check**

1. Inputs are present and complete for 5 traces:
1. trace_01_description.md
2. trace_02_description.md
3. trace_03_description.md
4. trace_04_description.md
5. trace_05_description.md
6. Matching signal CSVs exist for all 5 traces in the same folder.

2. No Task 3.2 submission scaffold exists yet:
1. No submissions/task-3.2 directory currently.
2. No zips-3.2 packaging directory currently.

3. No Task 3.2 automation scripts exist yet:
1. No manage-3.2 script under scripts.
2. No verify-3.2 script under scripts.
3. Dispatcher in verify-readiness.sh currently includes up to 3.1 by default.

4. Reuse assets already available:
1. Reusable TL-UL CSR driver in prior submissions, for example tl_ul_agent.py.
2. Good DUT-specific helper patterns in:
   1. helpers.py
   2. helpers.py
3. UART/SPI starter tests in:
   1. test_nexus_uart.py
   2. test_citadel_spi.py

5. Schema conflict detected and resolved:
1. Task page uses failure_XX and test_repro_XX naming in task_3_2_trace_detective.md.
2. Submission requirements use trace_XX and repro_XX naming in submission_requirements.md.
3. Based on prior 3.1 lesson learned, we should prioritize submission_requirements naming for parser safety.

---

**Gap Matrix**

1. Required Task 3.2 submission tree: Missing.
2. Required analysis YAML files (trace_01..05): Missing.
3. Required reproduction tests (repro_01..05): Missing.
4. Required metadata and methodology: Missing.
5. Required Makefile with run_repro target: Missing.
6. Packaging and readiness scripts for 3.2: Missing.
7. Prompt evidence packaging for 3.2: Missing.

---

**Execution Plan (Audit → Build → Validate)**

1. Structure and Schema Lock
1. Create submissions/task-3.2/submission-3.2 with analysis, reproduction_tests, prompts, methodology.md, Makefile, metadata.yaml.
2. Use submission_requirements schema keys exactly for trace_01..05.
3. Include summary.md as an additional judge-facing artifact for clarity and traceability.

2. Technical Analysis Authoring
1. For each trace, extract:
   1. manifestation_cycle from trace symptom.
   2. root_cause_cycle from first divergence.
   3. root_cause_file and root_cause_line from RTL in:
      1. warden_timer.sv
      2. nexus_uart.sv
      3. citadel_spi.sv
      4. aegis_aes.sv
      5. rampart_i2c.sv
2. Build signal_trace chain symptom-to-cause with cycle-accurate notes.

3. Reproduction Test Development
1. Implement reproduction_tests/repro_01.py through repro_05.py as minimal cocotb tests.
2. Keep tests deterministic and under 5000 cycles each.
3. Assert only target behavior so failures are specific and actionable.
4. Reuse TL-UL driver and existing DUT helper patterns to reduce risk and speed up bring-up.

4. Build and Run Flow
1. Implement Makefile targets:
   1. compile
   2. simulate
   3. coverage
   4. clean
   5. run_repro
2. Support SIM=icarus and SIM=verilator in the same submission flow.

5. Automation and Readiness
1. Add scripts/manage-3.2-submissions.sh using 3.1 script structure as baseline.
2. Add scripts/verify-3.2-readiness.sh with ZIP-first checks:
   1. package and extract
   2. required file and key validation
   3. make compile
   4. run_repro smoke behavior
   5. forbidden artifact scan
3. Extend verify-readiness.sh and README.md for Task 3.2 integration.
4. Extend prompt evidence regeneration script so Task 3.2 prompts are chunked in the same style as prior tasks.

6. Final Validation and Packaging
1. Run task-specific manager and verifier.
2. Run unified verifier with task 3.2.
3. Confirm final zip at submissions/zips-3.2/submission-3.2.zip.
4. Commit and push only Task 3.2 files and script integrations.

---

**Important Risk Controls**

1. Since inputs are CSV traces (not raw VCD files), we will treat provided CSV as the trusted waveform slice and avoid guessing unobserved transitions.
2. Some described bugs appear not to be present in current workspace RTL for local runs, so local validation will focus on scenario correctness and clean behavior while preserving evaluator-side buggy detection intent.
3. Keep naming and key schema aligned to submission_requirements first to avoid automated parser loss.

