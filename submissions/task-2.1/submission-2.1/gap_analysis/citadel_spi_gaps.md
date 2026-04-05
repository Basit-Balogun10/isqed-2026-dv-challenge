# citadel_spi Coverage Gaps

## Coverage Snapshot

- Line coverage: 57.17%
- Branch coverage: 22.08%

## Uncovered Code Regions

| Gap ID | File | Line Range | Reason Uncovered |
|--------|------|------------|------------------|
| GAP-013 | duts/citadel_spi/citadel_spi.sv | 126-141 | Baseline traffic does not vary command direction/speed/csaat combinations enough to activate full command-context handling. |
| GAP-014 | duts/citadel_spi/citadel_spi.sv | 452-459 | Command CSR writes are not stressed under full/near-full FIFO and invalid command combinations. |
| GAP-015 | duts/citadel_spi/citadel_spi.sv | 757-765 | CPOL/CPHA edge combinations are under-sampled, so edge-aligned bit transfer and first-bit-out handling remain partially uncovered. |
| GAP-016 | duts/citadel_spi/citadel_spi.sv | 773-780 | Few multi-segment CSAAT chains are executed, limiting coverage of command pop and continuation logic. |

## Unhit Functional Coverage Bins (Estimated From VPlan)

| Gap ID | Coverpoint | Bin Name | Required Stimulus |
|--------|------------|----------|-------------------|
| GAP-013 | vp_scenario_id | VP-SPI-003, VP-SPI-005, VP-SPI-009 | Issue command segments across TX/RX/BIDIR directions, speed modes, and CSAAT settings to validate active command bookkeeping. |
| GAP-014 | vp_scenario_id | VP-SPI-007, VP-SPI-011 | Drive command writes that exercise valid and invalid direction/length combinations under FIFO pressure. |
| GAP-015 | vp_scenario_id | VP-SPI-001, VP-SPI-002, VP-SPI-015 | Execute transfers in all SPI modes and verify sample/output edge behavior at bit boundaries. |
| GAP-016 | vp_scenario_id | VP-SPI-010, VP-SPI-016 | Run long CSAAT command chains and verify continuous chip-select behavior across segment boundaries. |

## Root Cause And Intent

### GAP-013 - active_command_context
- Root cause: Baseline traffic does not vary command direction/speed/csaat combinations enough to activate full command-context handling.
- Test intent: Issue command segments across TX/RX/BIDIR directions, speed modes, and CSAAT settings to validate active command bookkeeping.

### GAP-014 - command_decode_write_path
- Root cause: Command CSR writes are not stressed under full/near-full FIFO and invalid command combinations.
- Test intent: Drive command writes that exercise valid and invalid direction/length combinations under FIFO pressure.

### GAP-015 - data_transfer_bit_edge_logic
- Root cause: CPOL/CPHA edge combinations are under-sampled, so edge-aligned bit transfer and first-bit-out handling remain partially uncovered.
- Test intent: Execute transfers in all SPI modes and verify sample/output edge behavior at bit boundaries.

### GAP-016 - segment_chaining_csaat
- Root cause: Few multi-segment CSAAT chains are executed, limiting coverage of command pop and continuation logic.
- Test intent: Run long CSAAT command chains and verify continuous chip-select behavior across segment boundaries.
