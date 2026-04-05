# rampart_i2c Coverage Gaps

## Coverage Snapshot

- Line coverage: 49.33%
- Branch coverage: 23.49%

## Uncovered Code Regions

| Gap ID | File | Line Range | Reason Uncovered |
|--------|------|------------|------------------|
| GAP-025 | duts/rampart_i2c/rampart_i2c.sv | 748-775 | Single-host happy-path tests do not create arbitration-loss races during address bit drive/sample windows. |
| GAP-026 | duts/rampart_i2c/rampart_i2c.sv | 851-867 | ACK-driven command chaining through write->read/restart branches is only lightly exercised. |
| GAP-027 | duts/rampart_i2c/rampart_i2c.sv | 953-970 | Repeated-start timing path is under-covered because command sequences rarely chain restart immediately after prior transactions. |
| GAP-028 | duts/rampart_i2c/rampart_i2c.sv | 1205-1218 | Target-mode stretch release depends on FIFO availability races that are not created by baseline target tests. |

## Unhit Functional Coverage Bins (Estimated From VPlan)

| Gap ID | Coverpoint | Bin Name | Required Stimulus |
|--------|------------|----------|-------------------|
| GAP-025 | vp_scenario_id | VP-I2C-012, VP-I2C-013, VP-I2C-022 | Run multi-master contention scenarios to trigger host arbitration loss during address transmission. |
| GAP-026 | vp_scenario_id | VP-I2C-007, VP-I2C-015, VP-I2C-018 | Exercise write-ack branch fanout including restart, read-command follow-up, and additional write commands. |
| GAP-027 | vp_scenario_id | VP-I2C-004, VP-I2C-010, VP-I2C-020 | Generate repeated-start command sequences and validate timing counters for tsu_sta/thd_sta transitions. |
| GAP-028 | vp_scenario_id | VP-I2C-016, VP-I2C-017, VP-I2C-024 | Force target clock stretching and validate both release paths: TX data arrival and ACQ space availability. |

## Root Cause And Intent

### GAP-025 - host_addr_shift_and_arbitration
- Root cause: Single-host happy-path tests do not create arbitration-loss races during address bit drive/sample windows.
- Test intent: Run multi-master contention scenarios to trigger host arbitration loss during address transmission.

### GAP-026 - host_write_ack_command_chaining
- Root cause: ACK-driven command chaining through write->read/restart branches is only lightly exercised.
- Test intent: Exercise write-ack branch fanout including restart, read-command follow-up, and additional write commands.

### GAP-027 - host_repeated_start_timing
- Root cause: Repeated-start timing path is under-covered because command sequences rarely chain restart immediately after prior transactions.
- Test intent: Generate repeated-start command sequences and validate timing counters for tsu_sta/thd_sta transitions.

### GAP-028 - target_clock_stretch_release
- Root cause: Target-mode stretch release depends on FIFO availability races that are not created by baseline target tests.
- Test intent: Force target clock stretching and validate both release paths: TX data arrival and ACQ space availability.
