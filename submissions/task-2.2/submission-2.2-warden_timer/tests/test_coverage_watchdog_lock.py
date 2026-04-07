"""Coverage-closing watchdog lock test for Task 2.2 warden_timer."""

import cocotb
from cocotb.clock import Clock

from testbench.functional_coverage import (
    sample_bark_threshold,
    sample_bite_threshold,
    sample_pet_event,
    sample_wd_ctrl_value,
)
from testbench.tl_ul_agent import TlUlDriver

ADDR_WATCHDOG_CTRL = 0x1C
ADDR_WATCHDOG_BARK_THRESH = 0x20
ADDR_WATCHDOG_BITE_THRESH = 0x24
ADDR_WATCHDOG_PET = 0x28
ADDR_WATCHDOG_COUNT = 0x2C


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    tl = TlUlDriver(dut, clk_signal="clk_i")
    await tl.reset(rst_signal="rst_ni")
    return tl


@cocotb.test()
async def test_coverage_watchdog_lock(dut):
    """Task 2.2 coverage test: exercise watchdog enable/lock and threshold write paths."""
    tl = await setup(dut)

    await tl.write_reg(ADDR_WATCHDOG_BARK_THRESH, 0x00000040)
    await tl.write_reg(ADDR_WATCHDOG_BITE_THRESH, 0x00000080)
    bark = await tl.read_reg(ADDR_WATCHDOG_BARK_THRESH)
    bite = await tl.read_reg(ADDR_WATCHDOG_BITE_THRESH)
    assert bark == 0x00000040, f"BARK threshold readback mismatch: {bark:#010x}"
    assert bite == 0x00000080, f"BITE threshold readback mismatch: {bite:#010x}"
    sample_bark_threshold(bark)
    sample_bite_threshold(bite)

    # Set wd_enable and wd_lock bits to visit lock-gated write behavior.
    await tl.write_reg(ADDR_WATCHDOG_CTRL, 0x3)
    ctrl_locked = await tl.read_reg(ADDR_WATCHDOG_CTRL)
    assert (
        ctrl_locked & 0x3
    ) == 0x3, f"WATCHDOG_CTRL expected enable+lock set: {ctrl_locked:#010x}"
    sample_wd_ctrl_value(ctrl_locked)

    # Try to disable after lock; implementation should keep lock asserted.
    await tl.write_reg(ADDR_WATCHDOG_CTRL, 0x0)
    ctrl_after = await tl.read_reg(ADDR_WATCHDOG_CTRL)
    assert (
        ctrl_after & 0x2
    ) == 0x2, f"wd_lock must remain asserted after lock: {ctrl_after:#010x}"
    sample_wd_ctrl_value(ctrl_after)

    # Pet path should be executable under enabled watchdog mode.
    await tl.write_reg(ADDR_WATCHDOG_PET, 0x1)
    sample_pet_event()
    _ = await tl.read_reg(ADDR_WATCHDOG_COUNT)
