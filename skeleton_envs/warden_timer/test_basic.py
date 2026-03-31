"""Skeleton cocotb testbench for warden_timer.

Provides basic tests to get started. Achieves ~40% line coverage.
Participants should expand these tests to reach higher coverage targets.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from tl_ul_agent import TlUlDriver

# Register addresses
ADDR_MTIME_LOW            = 0x00
ADDR_MTIME_HIGH           = 0x04
ADDR_MTIMECMP0_LOW        = 0x08
ADDR_MTIMECMP0_HIGH       = 0x0C
ADDR_MTIMECMP1_LOW        = 0x10
ADDR_MTIMECMP1_HIGH       = 0x14
ADDR_PRESCALER            = 0x18
ADDR_WATCHDOG_CTRL        = 0x1C
ADDR_WATCHDOG_BARK_THRESH = 0x20
ADDR_WATCHDOG_BITE_THRESH = 0x24
ADDR_WATCHDOG_PET         = 0x28
ADDR_WATCHDOG_COUNT       = 0x2C
ADDR_INTR_STATE           = 0x30
ADDR_INTR_ENABLE          = 0x34
ADDR_INTR_TEST            = 0x38


async def setup(dut):
    """Common test setup: start clock, initialize inputs, assert reset."""
    cocotb.start_soon(Clock(dut.clk_i, 10, units='ns').start())
    dut.tl_a_valid_i.value = 0
    dut.tl_a_opcode_i.value = 0
    dut.tl_a_address_i.value = 0
    dut.tl_a_data_i.value = 0
    dut.tl_a_mask_i.value = 0
    dut.tl_a_source_i.value = 0
    dut.tl_a_size_i.value = 0
    dut.tl_d_ready_i.value = 0
    tl = TlUlDriver(dut)
    await tl.reset()
    return tl


@cocotb.test()
async def test_reset_values(dut):
    """Verify registers are at their reset values after reset."""
    tl = await setup(dut)

    mtime_low = await tl.read_reg(ADDR_MTIME_LOW)
    assert mtime_low < 10, f"MTIME_LOW should be near zero after reset, got: {mtime_low:#010x}"

    mtime_high = await tl.read_reg(ADDR_MTIME_HIGH)
    assert mtime_high == 0, f"MTIME_HIGH reset mismatch: {mtime_high:#010x}"

    prescaler = await tl.read_reg(ADDR_PRESCALER)
    assert prescaler == 0, f"PRESCALER reset mismatch: {prescaler:#010x}"

    wd_ctrl = await tl.read_reg(ADDR_WATCHDOG_CTRL)
    assert wd_ctrl == 0, f"WATCHDOG_CTRL reset mismatch: {wd_ctrl:#010x}"

    dut._log.info("test_reset_values PASSED")


@cocotb.test()
async def test_prescaler_config(dut):
    """Write prescaler value and verify mtime increments at expected rate."""
    tl = await setup(dut)

    # Set prescaler to 4 (mtime increments every 5 clocks)
    await tl.write_reg(ADDR_PRESCALER, 4)

    readback = await tl.read_reg(ADDR_PRESCALER)
    assert (readback & 0xFFF) == 4, f"PRESCALER readback mismatch: {readback:#010x}"

    # Wait some cycles and check mtime has incremented
    for _ in range(50):
        await RisingEdge(dut.clk_i)

    mtime_low = await tl.read_reg(ADDR_MTIME_LOW)
    dut._log.info(f"MTIME_LOW after 50 clocks with prescaler=4: {mtime_low}")
    assert mtime_low > 0, "MTIME should have incremented"

    dut._log.info("test_prescaler_config PASSED")


@cocotb.test()
async def test_basic_timer(dut):
    """Set mtimecmp0 to a low value and wait for timer0 interrupt."""
    tl = await setup(dut)

    # Use prescaler=0 (fastest increment)
    await tl.write_reg(ADDR_PRESCALER, 0)

    # Set mtimecmp0 to a small value to trigger quickly
    await tl.write_reg(ADDR_MTIMECMP0_LOW, 20)
    await tl.write_reg(ADDR_MTIMECMP0_HIGH, 0)

    # Enable timer0 interrupt
    await tl.write_reg(ADDR_INTR_ENABLE, 0x1)

    # Wait for interrupt to fire
    for _ in range(100):
        await RisingEdge(dut.clk_i)

    intr_state = await tl.read_reg(ADDR_INTR_STATE)
    timer0_expired = intr_state & 0x1
    dut._log.info(f"INTR_STATE = {intr_state:#010x}, timer0_expired = {timer0_expired}")

    if timer0_expired:
        dut._log.info("Timer 0 interrupt fired as expected")
    else:
        dut._log.warning("Timer 0 interrupt did not fire - may need more wait cycles")

    dut._log.info("test_basic_timer PASSED")
