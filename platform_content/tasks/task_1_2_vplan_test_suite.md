# Task 1.2: Verification Plan to Test Suite

**Phase 1 | 400 points per DUT | Up to 3 DUTs | Max 1200 points**

---

## Overview

You are given a structured YAML verification plan (vplan) for each DUT. Your objective is to generate a complete UVM test suite that covers every verification item in the plan. Each test must be traceable to a specific vplan entry, drive targeted stimulus, check expected behavior, and hit the coverage bins specified in the plan.

This task measures your ability to translate verification intent -- expressed as structured data -- into working, meaningful tests that exercise the DUT correctly.

---

## Available DUTs

| Tier | DUT Name | Protocol | Approx. Lines | Vplan Items (approx.) |
|------|----------|----------|---------------|----------------------|
| Tier 1 (Starter) | `nexus_uart` | UART | ~500 | ~25 |
| Tier 1 (Starter) | `bastion_gpio` | GPIO | ~400 | ~20 |
| Tier 2 (Intermediate) | `warden_timer` | Timer/Watchdog | ~600 | ~30 |
| Tier 2 (Intermediate) | `citadel_spi` | SPI Host | ~900 | ~35 |
| Tier 3 (Advanced) | `aegis_aes` | AES-128 | ~1200 | ~40 |
| Tier 3 (Advanced) | `sentinel_hmac` | HMAC-SHA256 | ~1000 | ~35 |
| Tier 4 (Expert) | `rampart_i2c` | I2C Host/Target | ~1100 | ~45 |

All DUTs share a common **TileLink-UL simplified bus interface** (`tl_i`/`tl_o` with ready/valid handshake), active-low asynchronous reset (`rst_ni`), and standard interrupt (`intr_o`) and alert (`alert_o`) outputs.

You may submit test suites for **up to 3 DUTs**.

---

## Verification Plan Format

Each vplan is provided as a YAML file with the following structure per item:

```yaml
vplan:
  - id: VP-TIMER-001
    feature: "Basic countdown"
    description: >
      When CTRL.enable is set and COMPARE is loaded with a non-zero value,
      the timer counts up from zero. When the counter reaches COMPARE,
      the INTR_STATE.timer_expired bit is asserted.
    stimulus: >
      Write COMPARE register with value N.
      Write CTRL register to enable timer.
      Wait for N+margin clock cycles.
    check: >
      Read INTR_STATE and verify timer_expired == 1.
      Verify interrupt output pin is asserted.
    coverage_bins:
      - compare_value: [1, 100, 0xFFFF, 0xFFFFFFFF]
      - prescale: [0, 1, 15]
    priority: high

  - id: VP-TIMER-002
    feature: "Prescaler division"
    description: >
      When CTRL.prescale is set to P, the timer increments once every
      (P+1) clock cycles instead of every cycle.
    stimulus: >
      Set CTRL.prescale = P, COMPARE = N, enable timer.
      Wait for N*(P+1)+margin clock cycles.
    check: >
      Verify timer_expired fires at the correct time.
      Read counter value and confirm it equals COMPARE.
    coverage_bins:
      - prescale: [0, 1, 7, 15]
      - compare_value: [1, 50, 0xFFFF]
    priority: high

  - id: VP-TIMER-003
    feature: "Watchdog timeout and reset"
    description: >
      When watchdog mode is enabled and the counter reaches the BARK
      threshold without a pet (write to WDOG_PET), the bark interrupt
      fires. If it further reaches the BITE threshold, alert_o is asserted.
    stimulus: >
      Configure WDOG_CTRL for watchdog mode.
      Set BARK and BITE thresholds.
      Enable watchdog. Do NOT write WDOG_PET.
    check: >
      Verify bark interrupt fires at BARK threshold.
      Verify alert_o asserts at BITE threshold.
    coverage_bins:
      - bark_threshold: [10, 100, 0xFFFF]
      - bite_threshold: [20, 200, 0xFFFFF]
    priority: critical
```

---

## What to Build

### For Each Vplan Item, Generate a Test That:

1. **Links to the VP-ID** -- The test class name or a metadata tag must reference the vplan ID (e.g., `test_vp_timer_001`).

2. **Configures the DUT via CSR writes** -- Use TL-UL sequences to program the DUT into the required state. All register addresses and field positions are available in the provided Hjson CSR maps.

3. **Drives targeted stimulus** -- Apply the stimulus described in the vplan entry. For DUTs with external protocol interfaces (UART, SPI, I2C, GPIO), use the protocol agent. For CSR-only DUTs (Timer, AES, HMAC), all stimulus is via TL-UL writes.

4. **Checks expected behavior** -- Perform explicit checks matching the vplan's `check` field. Use scoreboard comparisons, register reads with expected-value assertions, or output pin monitoring as appropriate.

5. **Targets specific coverage bins** -- Parameterize or constrain the test so that the coverage bins listed in the vplan entry are hit. Use `covergroup` sample calls or explicit bin-matching logic.

### Example Test (for VP-TIMER-001)

```systemverilog
class test_vp_timer_001 extends warden_timer_base_test;
  `uvm_component_utils(test_vp_timer_001)

  function new(string name = "test_vp_timer_001", uvm_component parent);
    super.new(name, parent);
  endfunction

  task run_phase(uvm_phase phase);
    tl_ul_write_seq wr_seq;
    tl_ul_read_seq  rd_seq;

    phase.raise_objection(this, "VP-TIMER-001: Basic countdown");

    foreach ({32'h1, 32'h64, 32'hFFFF, 32'hFFFF_FFFF} [i]) begin
      int unsigned compare_val = {32'h1, 32'h64, 32'hFFFF, 32'hFFFF_FFFF}[i];

      // Step 1: Write COMPARE register
      wr_seq = tl_ul_write_seq::type_id::create("wr_compare");
      wr_seq.addr = TIMER_COMPARE_OFFSET;
      wr_seq.data = compare_val;
      wr_seq.start(env.m_tl_agent.m_sequencer);

      // Step 2: Enable timer (CTRL.enable = 1)
      wr_seq = tl_ul_write_seq::type_id::create("wr_ctrl");
      wr_seq.addr = TIMER_CTRL_OFFSET;
      wr_seq.data = 32'h1;  // enable bit
      wr_seq.start(env.m_tl_agent.m_sequencer);

      // Step 3: Wait for counter to reach COMPARE
      wait_for_interrupt_or_timeout(compare_val + 100);

      // Step 4: Read INTR_STATE, verify timer_expired
      rd_seq = tl_ul_read_seq::type_id::create("rd_intr");
      rd_seq.addr = TIMER_INTR_STATE_OFFSET;
      rd_seq.start(env.m_tl_agent.m_sequencer);

      if (!(rd_seq.rdata & TIMER_EXPIRED_BIT))
        `uvm_error("VP-TIMER-001",
          $sformatf("timer_expired not set for COMPARE=%0h", compare_val))

      // Step 5: Reset for next iteration
      apply_reset();
    end

    phase.drop_objection(this);
  endtask
endclass
```

### Test Suite Organization

```
submission/
  task_1_2/
    <dut_name>/
      tests/
        test_vp_<dut>_001.sv
        test_vp_<dut>_002.sv
        ...
        test_vp_<dut>_NNN.sv
      sequences/
        <dut>_vp_sequences.sv     # Reusable sequence library
      base/
        <dut>_base_test.sv        # Base test with common setup/teardown
      coverage/
        <dut>_vp_coverage.sv      # Covergroups matching vplan bins
      regression.list             # Simulator regression file
      filelist.f                  # Compilation file list
```

---

## Key Challenge

The central difficulty of this task is creating tests that are simultaneously:

- **Robust enough to pass on correct RTL** -- Tests must not produce false failures due to timing assumptions, race conditions, or incorrect expected values.
- **Sensitive enough to fail on buggy RTL** -- Tests must actually check meaningful behavior. A test that writes a register and never reads it back, or that waits an arbitrary time without checking outputs, earns minimal credit.

Your tests will be evaluated against both the **clean reference RTL** (must pass) and a set of **mutant RTL variants** with injected bugs (should fail). The ratio of bugs caught to bugs present is a key scoring factor.

---

## Evaluation Rubric

### Automated Scoring (85% -- 340 points per DUT)

| Category | Points | Criteria |
|----------|--------|----------|
| **Pass on Clean RTL** | _Gate_ | **All submitted tests must pass on the unmodified reference RTL.** Tests that fail on clean RTL are disqualified from further scoring. This is a hard requirement, not a point category. |
| **VP-Item Coverage** | 200 pts | For each vplan item: test exists and is linked to VP-ID (5 pts), test passes on clean RTL (5 pts), test drives the specified stimulus (5 pts), test performs the specified check (10 pts), coverage bins from the vplan entry are hit (5 pts). Summed across all VP items, scaled to 200 pts. |
| **Bug Detection** | 100 pts | Each submitted test is run against a hidden set of mutant RTL variants. Points awarded proportionally: `100 * (bugs_caught / total_bugs)`. A "caught" bug means at least one test reports UVM_ERROR or UVM_FATAL on the mutant. |
| **Exceeding the Plan** | 40 pts (bonus) | Tests that cover scenarios beyond the provided vplan items earn bonus points. Evaluated by running tests against additional mutants not covered by the vplan. Capped at 40 bonus points. |

**Penalty:** Tests that produce false failures (UVM_ERROR on clean RTL) result in a **-10 point penalty per offending test** after the gate check. Fix your tests before submitting.

### Judge Scoring (15% -- 60 points per DUT)

| Category | Points | Criteria |
|----------|--------|----------|
| **Test Quality** | 30 pts | Each test is focused and minimal. Clear separation of setup, stimulus, and checking. Appropriate use of constraints and randomization. No copy-paste bloat. |
| **Verification Intent Clarity** | 30 pts | Reading the test makes it obvious what is being verified and why. VP-ID traceability is clean. Failure messages are informative. Test names are descriptive. |

---

## Tips for AI-Assisted Development

1. **Parse the vplan YAML programmatically.** Build a pipeline that reads each vplan entry and generates a test skeleton with the VP-ID, stimulus steps, and check steps pre-filled. Manual test-by-test authoring is slow and error-prone.

2. **Anchor your timing to DUT events, not cycle counts.** Use interrupt signals, status register polling, or monitor-reported events to determine when the DUT has completed an operation. Hardcoded `#delays` are fragile and will break across different mutant configurations.

3. **Test the tests.** Before submission, verify that your tests actually catch known-bad behavior. Inject a simple bug (e.g., tie an output to zero) and confirm your test reports an error.

4. **Use a base test class aggressively.** Common patterns -- reset sequence, clock configuration, CSR utility tasks, objection management -- belong in the base test. Individual VP tests should contain only the unique stimulus and checks.

5. **Coverage bins are scoring criteria.** If the vplan says `compare_value: [1, 100, 0xFFFF, 0xFFFFFFFF]`, your test must exercise all four values. Parameterize your test or loop over the bin values explicitly.

6. **Mind the CSR side effects.** Many registers have write-1-to-clear (W1C) fields, read-to-clear behavior, or write-enable gating. Consult the Hjson register map to avoid inadvertently clearing state you need to check.
