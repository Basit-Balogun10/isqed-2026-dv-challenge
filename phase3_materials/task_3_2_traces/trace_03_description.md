# Trace 03: Citadel SPI — CS Hold Time Violation

## Failing Assertion

```
ASSERTION FAILED: assert_csn_hold_time
  Location: citadel_spi_sva.sv:55
  Message: "CSn must remain asserted (low) for at least csn_trail SCLK periods after last data edge"
  Failure time: cycle 300
```

## Spec Requirement

From the Citadel SPI Specification, Section 4.2.3:

> **Chip Select Timing:** The CS (chip select) signal timing is controlled by three
> parameters in CONFIGOPTS:
> - csn_lead: Minimum SCLK periods between CS assertion and first SCLK edge
> - csn_trail: Minimum SCLK periods between last SCLK edge and CS deassertion
> - csn_idle: Minimum SCLK periods between CS deassertion and next CS assertion
>
> The SPI controller SHALL hold CS low for at least csn_trail periods after the
> final data clock edge before releasing CS. Violating this timing may cause
> data corruption on the target device.

## Test Scenario

1. Configure SPI: CPOL=0, CPHA=0 (Mode 0), clkdiv=4, csn_lead=2, csn_trail=4, csn_idle=3
2. Select chip 0 (CSID=0)
3. Enable SPI engine
4. Send a single byte (0xA5) with BIDIR mode, CSAAT=0 (release CS after transfer)
5. Monitor timing: CS should remain low for 4 SCLK periods after the last data edge
6. Verify CS deassertion timing

## Observed Behavior

After the last data bit is clocked (bit 0), the FSM transitions from DATA_XFER to
CS_HOLD. However, the CS_HOLD state uses a timing counter that counts from 0 to
csn_trail-1 instead of 0 to csn_trail. This results in CS being held for only 3 SCLK
periods instead of the configured 4. The CS line goes high one SCLK period too early.

The timing_cnt counter in the CS_HOLD state increments and compares against
csn_trail, but the comparison uses `>= reg_csn_trail` which triggers one tick
early because the counter starts at 0 (first count = 0, not 1).

## Signal Trace File

See `trace_03_signals.csv` for cycle-by-cycle signal values.
Key signals:
- `csn_o[0]` — chip select output (active low)
- `sclk_o` — serial clock output
- `fsm_state` — SPI FSM state (IDLE=0, CS_SETUP=1, DATA_XFER=2, CS_HOLD=3, CS_IDLE=4)
- `timing_cnt` — timing counter for CS setup/hold/idle phases
- `bit_cnt` — bit counter within current byte
- `byte_cnt` — byte counter within current command segment
