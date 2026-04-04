# Task 1.3 Full Evaluation Report (2026-04-04, Corrected)

## Scope Executed
- Package-first run from submission zip (platform-equivalent flow).
- Extracted zip and ran `make generate` inside extracted artifact.
- Runtime matrix executed for all generated DUT suites on both simulators.
- Correction applied: prior `aegis_aes@icarus` skip was a harness assumption, not a proven simulator limitation for this generated suite.

Execution evidence:
- Full matrix artifact: `WORKDIR=/tmp/task13-full-eval-LijOFC` (13 executed runs, 1 historical skip gate).
- Empirical correction run (extracted zip + explicit DUT path): `PROOF_LOG=/tmp/task13-aes-proof3-zHwxjL/aes_icarus.log`.
- Correction-run summary line: `TESTS=5 PASS=5 FAIL=0 SKIP=0`.
- Correction-run exit code: `SIM_EC=0`.

## Generator CLI Validity (Per DUT Map)
- aegis_aes: PASS
- bastion_gpio: PASS
- citadel_spi: PASS
- nexus_uart: PASS
- rampart_i2c: PASS
- sentinel_hmac: PASS
- warden_timer: PASS

## Runtime Matrix Results (Corrected)
- aegis_aes@icarus: PASS (TESTS=5, FAIL=0)
- bastion_gpio@icarus: PASS (TESTS=5, FAIL=0)
- citadel_spi@icarus: PASS (TESTS=5, FAIL=0)
- nexus_uart@icarus: PASS (TESTS=5, FAIL=0)
- rampart_i2c@icarus: PASS (TESTS=5, FAIL=0)
- sentinel_hmac@icarus: PASS (TESTS=5, FAIL=0)
- warden_timer@icarus: PASS (TESTS=5, FAIL=0)
- aegis_aes@verilator: PASS (TESTS=5, FAIL=0)
- bastion_gpio@verilator: PASS (TESTS=5, FAIL=0)
- citadel_spi@verilator: PASS (TESTS=5, FAIL=0)
- nexus_uart@verilator: PASS (TESTS=5, FAIL=0)
- rampart_i2c@verilator: PASS (TESTS=5, FAIL=0)
- sentinel_hmac@verilator: PASS (TESTS=5, FAIL=0)
- warden_timer@verilator: PASS (TESTS=5, FAIL=0)

Summary counts:
- Executed runs: 14
- PASS: 14
- FAIL: 0
- SKIP: 0

## Required Category Coverage
Task spec requires 6 categories. Runtime executes 5 test functions because RW and RO are combined in one function:
- Reset value: `test_csr_reset_values`
- Read/write (RW): covered inside `test_csr_rw_ro_access`
- Read-only (RO): covered inside `test_csr_rw_ro_access`
- W1C: `test_csr_w1c_behavior`
- Bit isolation: `test_csr_bit_isolation`
- Address decode: `test_csr_address_decode`

## Conclusion
- Submission packaging, generation, and runtime behavior are fully green under package-first evaluation.
- Dual-simulator compliance is satisfied for all DUT/simulator pairs.
- No active `aegis_aes@icarus` skip caveat is required for this generated Task 1.3 suite.
