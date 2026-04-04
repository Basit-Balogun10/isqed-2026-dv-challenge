- This keeps DUT source untouched and makes assertion packs portable and judge-friendly.

4. Manifest and traceability.
- Generate assertion_manifest.yaml for automated checks.
- Also provide assertion_manifest.csv for task-doc alignment.
- Every assertion will include a short spec_ref mapping to spec clauses in rampart_i2c_spec.md and sentinel_hmac_spec.md.

5. Test harness for assertion exercise.
- Implement tests/test_with_assertions.py per DUT using existing TL-UL helpers.
- Ensure clean RTL pass path is stable and deterministic.
- Keep optional fire-path checks isolated so they do not contaminate clean regression runs.

6. Makefile and simulator compliance.
- Ensure assertion files are always compiled with DUT.
- Enforce dual-simulator execution targets for Icarus and Verilator.
- Add warning controls only when needed to avoid false tool failures.

7. Package-first readiness flow for 1.4.
- Add scripts/manage-1.4-submissions.sh for package/extract/verify/status.
- Add scripts/verify-1.4-readiness.sh for zip-first structural checks and runtime smoke tests.
- Update verify-readiness.sh to include 1.4 dispatch.

8. Final methodology and submission integrity.
- Write methodology with honest iteration/failure loops and AI evidence.
- Zip hygiene checks: no waveform artifacts, no results.xml bloat, required files only.
- Final answer to submit will be exact zip paths under submissions/zips-1.4.

**Definition Of Done For This Task Kickoff**
- Audit complete.
- DUT strategy selected.
- Risks and doc ambiguities identified with mitigation.
- End-to-end implementation plan ready with packaging and readiness gates.

Next natural step is execution of Phase 1 scaffolding plus first assertion set for rampart_i2c.  
1. Start with both DUT skeletons and 1.4 automation scripts.  
2. Start with rampart_i2c only first, then clone pattern to sentinel_hmac.  
3. Start by writing the reusable TL-UL protocol assertion library before DUT-specific assertions.Continued with AutopilotTask 1.4 kickoff is fully completed: I finished the repository audit, selected the recommended DUT pair, identified tooling and documentation constraints, and delivered a concrete execution plan modeled on the Task 1.3 workflow. I’m now formally marking this interaction complete as requested.



User: Aweseome, setup your todo accorindgly and jump in to execution/implemenattion. REmember we are on Path A (cocotb/open-source), I can see stuff like "Path A teams: SVA assertions are compiled alongside the DUT via the bind file. Your Makefile must include the bind file in compilation" in the specific requirements in #file:submission_requirements.md 

Let's get to work!

GitHub Copilot: I’m switching from planning to implementation now: first I’ll initialize a fresh Task 1.4 TODO list, then scaffold the two Path A DUT submissions and start coding assertion packs plus dual-simulator-ready Makefiles.

Created 7 todos

Before editing, I’m quickly pulling the DUT behavior details we’ll encode in assertions so we avoid brittle properties and keep clean-RTL false positives at zero.

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/rampart_i2c/rampart_i2c.sv#250-250), lines 250 to 620

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/sentinel_hmac/sentinel_hmac.sv#250-250), lines 250 to 520

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/specs/sentinel_hmac_spec.md)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/specs/rampart_i2c_spec.md#1-1), lines 1 to 280

I’ve captured the key CSR/protocol behavior; next I’m extracting the remaining FSM/output sections so our functional and liveness assertions are anchored to real control-path transitions, not guesses.

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/rampart_i2c/rampart_i2c.sv#620-620), lines 620 to 1040

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-rampart_i2c/tests/test_vp_001.py)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-sentinel_hmac/tests/test_vp_001.py)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/rampart_i2c/rampart_i2c.sv#1040-1040), lines 1040 to 1320

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/rampart_i2c/rampart_i2c.sv#1320-1320), lines 1320 to 1360

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/duts/sentinel_hmac/sentinel_hmac.sv#520-520), lines 520 to 796

Configuring a Python Environment
Completed with input: {
  "resourcePath": "/home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge"
}

I’ve gathered enough DUT internals to start coding safely. Next I’m creating the Task 1.4 submission skeletons and then adding conservative, simulator-friendly SVA sets plus cocotb smoke tests for both DUTs.

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-rampart_i2c/testbench/tl_ul_agent.py)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/assertions)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/tests)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/testbench)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/prompts)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/assertions)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/tests)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/testbench)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/prompts)

I’ve scaffolded both submission directories; now I’m adding shared cocotb plumbing and then writing the first full assertion set for rampart_i2c.

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/testbench/__init__.py)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/tests/__init__.py)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/testbench/__init__.py)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/tests/__init__.py)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/testbench/tl_ul_agent.py)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/testbench/tl_ul_agent.py)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/assertions/protocol_assertions.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/assertions/functional_assertions.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/assertions/structural_assertions.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/assertions/liveness_assertions.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/bind_file.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/assertion_manifest.yaml)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/tests/test_with_assertions.py)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.2/submission-1.2-rampart_i2c/metadata.yaml)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.3/submission-1.3/metadata.yaml)

Read [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.3/submission-1.3/Makefile)

Progress update: rampart_i2c assertion files, bind file, and test are in place. I’m now adding metadata/Makefile/methodology for rampart and then I’ll mirror the full stack for sentinel_hmac.

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/metadata.yaml)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/methodology.md)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/Makefile)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-rampart_i2c/prompts/README.md)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/assertions/protocol_assertions.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/assertions/functional_assertions.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/assertions/structural_assertions.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/assertions/liveness_assertions.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/bind_file.sv)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/assertion_manifest.yaml)

Retried with Autopilot

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/tests/test_with_assertions.py)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/metadata.yaml)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/methodology.md)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/Makefile)

Created [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4/submission-1.4-sentinel_hmac/prompts/README.md)

Both DUT submission skeletons are now created with assertion packs, bind wiring, Makefiles, tests, and metadata. I’m running static diagnostics next, then I’ll fix issues before dual-simulator runs.

Checked [](file:///home/abdulbasit/electrical-and-electronics-engineering/VLSI/isqed-2026-dv-challenge/submissions/task-1.4), 64 problems found
