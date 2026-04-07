"""Reference baseline smoke test for Task 2.2 warden_timer submission."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from testbench.functional_coverage import sample_prescaler, sample_wd_ctrl_value
from testbench.tl_ul_agent import TlUlDriver

ADDR_MTIME_LOW = 0x00
ADDR_MTIME_HIGH = 0x04
ADDR_PRESCALER = 0x18
ADDR_WATCHDOG_CTRL = 0x1C


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    tl = TlUlDriver(dut, clk_signal="clk_i")
    await tl.reset(rst_signal="rst_ni")
    return tl


@cocotb.test()
async def test_reference(dut):
    """Task 2.2 reference test: confirm reset defaults for key timer CSRs."""
    tl = await setup(dut)

    mtime_low = await tl.read_reg(ADDR_MTIME_LOW)
    mtime_high = await tl.read_reg(ADDR_MTIME_HIGH)
    prescaler = await tl.read_reg(ADDR_PRESCALER)
    wd_ctrl = await tl.read_reg(ADDR_WATCHDOG_CTRL)

    assert mtime_high == 0, f"MTIME_HIGH reset mismatch: {mtime_high:#010x}"
    assert (
        mtime_low < 16
    ), f"MTIME_LOW should be near zero after reset: {mtime_low:#010x}"
    assert prescaler == 0, f"PRESCALER reset mismatch: {prescaler:#010x}"
    assert wd_ctrl == 0, f"WATCHDOG_CTRL reset mismatch: {wd_ctrl:#010x}"

    sample_prescaler(prescaler)
    sample_wd_ctrl_value(wd_ctrl)

    # Keep a few cycles to ensure timer can run post-reset.
    for _ in range(5):
        await RisingEdge(dut.clk_i)
