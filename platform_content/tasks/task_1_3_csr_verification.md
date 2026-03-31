# Task 1.3: Register Verification Suite

**Phase 1 | 200 points flat (all DUTs) | Not per-DUT**

---

## Overview

Generate a comprehensive, fully automated CSR (Control and Status Register) regression suite from the machine-readable Hjson register maps provided for each DUT. The suite must verify the correctness of every register in every DUT: reset values, read/write behavior, access policies, and bit-level isolation.

This task is a **prime candidate for fully automated generation**. The winning approach will build a generative pipeline that reads the Hjson register description and emits a complete test suite with zero manual per-register code. The same pipeline must work across all 7 DUTs without modification.

---

## Available DUTs and Register Counts

| Tier | DUT Name | Approx. Registers | CSR Map File |
|------|----------|-------------------|--------------|
| Tier 1 | `nexus_uart` | ~12 | `nexus_uart.hjson` |
| Tier 1 | `bastion_gpio` | ~8 | `bastion_gpio.hjson` |
| Tier 2 | `warden_timer` | ~10 | `warden_timer.hjson` |
| Tier 2 | `citadel_spi` | ~15 | `citadel_spi.hjson` |
| Tier 3 | `aegis_aes` | ~14 | `aegis_aes.hjson` |
| Tier 3 | `sentinel_hmac` | ~12 | `sentinel_hmac.hjson` |
| Tier 4 | `rampart_i2c` | ~18 | `rampart_i2c.hjson` |

All registers are accessed via the common **TileLink-UL simplified bus interface** (`tl_i`/`tl_o` with ready/valid handshake). The base address for each DUT's register space is provided in the platform configuration.

---

## Input: Hjson Register Map

Each DUT's register map is provided in Hjson format (a human-friendly JSON superset). Here is an abbreviated example:

```hjson
{
  name: "warden_timer",
  registers: [
    {
      name: "CTRL",
      offset: "0x0",
      reset_val: "0x0",
      fields: [
        { name: "enable",   bits: "0",    access: "rw", reset: "0x0",
          desc: "Timer enable. 1 = counting, 0 = halted." }
        { name: "prescale", bits: "7:4",  access: "rw", reset: "0x0",
          desc: "Clock prescaler. Timer increments every (prescale+1) cycles." }
        { name: "step",     bits: "15:8", access: "rw", reset: "0x1",
          desc: "Counter step size per tick." }
      ]
    }
    {
      name: "COUNTER",
      offset: "0x4",
      reset_val: "0x0",
      fields: [
        { name: "value", bits: "31:0", access: "ro", reset: "0x0",
          desc: "Current counter value. Read-only." }
      ]
    }
    {
      name: "COMPARE",
      offset: "0x8",
      reset_val: "0xFFFFFFFF",
      fields: [
        { name: "value", bits: "31:0", access: "rw", reset: "0xFFFFFFFF",
          desc: "Counter comparison value." }
      ]
    }
    {
      name: "INTR_STATE",
      offset: "0xC",
      reset_val: "0x0",
      fields: [
        { name: "timer_expired", bits: "0", access: "rw1c", reset: "0x0",
          desc: "Timer expired interrupt. Write 1 to clear." }
      ]
    }
    // ... more registers
  ]
}
```

---

## Required Test Categories

Your generated suite must include the following test types for every applicable register and field:

### 1. Reset Value Test

After reset de-assertion, read every register and verify the value matches the `reset_val` from the Hjson map.

```systemverilog
// Auto-generated: Reset value test for CTRL (offset 0x0)
task test_reset_ctrl();
  tl_ul_read_seq rd;
  rd = tl_ul_read_seq::type_id::create("rd_ctrl");
  rd.addr = base_addr + 32'h0;
  rd.start(env.m_tl_agent.m_sequencer);
  check_value("CTRL reset", rd.rdata, 32'h0);
endtask
```

### 2. Read/Write Test

For each RW register, write a known pattern, read it back, and verify the written value is returned. Test with at least two patterns (e.g., `0x5555_5555` and `0xAAAA_AAAA` masked to writable bits).

### 3. Read-Only Test

For each RO register/field, write a non-reset value and read back. Verify the register value is unchanged (still equals its current/reset value). The write must have no effect.

### 4. Write-1-to-Clear (W1C) Test

For each W1C field, force the bit high (via stimulus or backdoor), then write 1 to clear it, and verify it returns to 0. Also verify that writing 0 does NOT clear the bit.

### 5. Bit Isolation Test (Walking Ones / Walking Zeros)

For each RW register, perform a walking-1 and walking-0 test across all writable bits. This verifies that writing one bit does not corrupt adjacent bits.

```
Walking-1: For each bit position i in writable_mask:
  Write (1 << i), read back, verify only bit i is set.
Walking-0: For each bit position i in writable_mask:
  Write (~(1 << i) & writable_mask), read back, verify only bit i is clear.
```

### 6. Address Decode Test

Write a unique value to each register, then read all registers back and verify no address aliasing or decode errors. This confirms each register occupies its specified offset without overlap.

---

## The Generative Pipeline

The ideal submission is not a collection of hand-written tests, but a **pipeline** consisting of:

```
  Hjson register map  -->  [Parser]  -->  [Generator]  -->  SystemVerilog test suite
       (input)                                                    (output)
```

**Parser:** Reads the Hjson file and extracts register metadata (name, offset, reset value, fields with bit ranges, access types).

**Generator:** For each register, emits the appropriate tests based on the access type of each field:
- `rw` fields: reset test + read/write test + bit isolation test
- `ro` fields: reset test + read-only test
- `rw1c` fields: reset test + W1C test
- All registers: address decode test

**Output:** A set of SystemVerilog test files and a regression list, ready to compile and run.

```python
# Example pipeline sketch (Python)
import hjson

def generate_csr_tests(hjson_path, dut_name, base_addr):
    with open(hjson_path) as f:
        regmap = hjson.load(f)

    tests = []
    for reg in regmap['registers']:
        name = reg['name']
        offset = int(reg['offset'], 16)
        reset = int(reg['reset_val'], 16)

        # Reset value test (always generated)
        tests.append(gen_reset_test(dut_name, name, base_addr + offset, reset))

        for field in reg['fields']:
            access = field['access']
            bits = parse_bits(field['bits'])
            mask = bits_to_mask(bits)

            if access == 'rw':
                tests.append(gen_rw_test(dut_name, name, field['name'],
                                         base_addr + offset, mask))
                tests.append(gen_bit_isolation_test(dut_name, name, field['name'],
                                                    base_addr + offset, mask))
            elif access == 'ro':
                tests.append(gen_ro_test(dut_name, name, field['name'],
                                         base_addr + offset, mask, reset))
            elif access == 'rw1c':
                tests.append(gen_w1c_test(dut_name, name, field['name'],
                                          base_addr + offset, mask))

    # Address decode test (one per DUT)
    tests.append(gen_addr_decode_test(dut_name, regmap['registers'], base_addr))

    return tests
```

---

## Submission Format

```
submission/
  task_1_3/
    generator/
      csr_test_gen.py            # The generative pipeline
      hjson_parser.py            # Hjson parsing utilities
      templates/                 # SystemVerilog templates (if using)
    generated/
      <dut_name>/
        csr_reset_test.sv
        csr_rw_test.sv
        csr_ro_test.sv
        csr_w1c_test.sv
        csr_bit_isolation_test.sv
        csr_addr_decode_test.sv
        csr_regression.list
        filelist.f
      ...                        # Repeat for each DUT
    Makefile                     # `make generate` runs the pipeline
```

The platform will run `make generate` and then compile/simulate the generated output. Both the generator and the generated tests are evaluated.

---

## Evaluation Rubric

### Automated Scoring (90% -- 180 points)

Scoring is **per register across all 7 DUTs**. The approximate total register count is ~89.

| Category | Points | Criteria |
|----------|--------|----------|
| **Reset Value Tests** | ~2 pts per register | Each register's reset value is correctly checked after reset de-assertion. Approx. 89 registers x 2 pts = ~178 pts, scaled to budget. |
| **RW / RO / W1C Tests** | ~3 pts per register | Correct access-type test for each register. RW registers tested with write-readback. RO registers confirmed unmodifiable. W1C fields tested with set-clear sequence. Approx. 89 registers x 3 pts = ~267 pts, scaled to budget. |
| **Bit Isolation** | Included in per-register | Walking-1 and walking-0 tests pass for all RW registers. |
| **Address Decode** | Included in per-DUT | No aliasing detected across the register space. |
| **Full Automation Bonus** | 50 pts | Awarded if the generator successfully produces a passing test suite for **all 7 DUTs** from their Hjson maps without any manual per-DUT intervention. The platform runs `make generate` once and evaluates all outputs. |

_Point allocation note: The per-register points are summed across all registers and DUTs, then scaled so that perfect per-register coverage equals 130 points. The automation bonus (50 pts) brings the automated total to 180 points._

### Judge Scoring (10% -- 20 points)

| Category | Points | Criteria |
|----------|--------|----------|
| **Generator Quality** | 20 pts | Pipeline architecture: clean parser/generator separation, use of templates, extensibility to new access types. Error handling for malformed Hjson. Code clarity and documentation within the generator itself. |

---

## Tips for AI-Assisted Development

1. **Treat this as a code-generation problem, not a verification problem.** The tests themselves are repetitive by design. The value is in the generator that produces them correctly and completely.

2. **Start with a single DUT, then generalize.** Get your pipeline working end-to-end on `bastion_gpio` (fewest registers), then run it on all 7 DUTs and fix any edge cases.

3. **Handle field masks carefully.** A register may have a mix of RW, RO, and reserved fields. Your write patterns must be masked to only target writable bits; otherwise, writes to reserved fields may cause undefined behavior.

4. **The Hjson format has quirks.** It allows trailing commas, unquoted keys, and `//` comments. Use an Hjson parser (e.g., Python's `hjson` package), not a plain JSON parser.

5. **W1C testing requires setup.** To test a W1C bit, you first need the bit to be set. For interrupt status registers, this means triggering the interrupt condition (or using a backdoor force if available). Plan your stimulus accordingly.

6. **The automation bonus is worth 50 points.** That is a significant chunk of the total. Prioritize making your pipeline fully general over hand-tuning individual register tests.
