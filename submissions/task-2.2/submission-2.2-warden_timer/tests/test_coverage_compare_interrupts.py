"""Annotate-driven comparator/interrupt closure test for Task 2.2 warden_timer."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from testbench.functional_coverage import (
    sample_bark_threshold,
    sample_bite_threshold,
    sample_compare_programming,
    sample_intr_enable,
    sample_pet_event,
    sample_prescaler,
    sample_timer_irq_source,
    sample_wd_ctrl_value,
)
from testbench.tl_ul_agent import TlUlDriver

ADDR_MTIMECMP0_LOW = 0x08
ADDR_MTIMECMP0_HIGH = 0x0C
ADDR_MTIMECMP1_LOW = 0x10
ADDR_MTIMECMP1_HIGH = 0x14
ADDR_PRESCALER = 0x18
ADDR_WATCHDOG_CTRL = 0x1C
ADDR_WATCHDOG_BARK_THRESH = 0x20
ADDR_WATCHDOG_BITE_THRESH = 0x24
ADDR_INTR_STATE = 0x30
ADDR_INTR_ENABLE = 0x34
ADDR_INTR_TEST = 0x38


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    tl = TlUlDriver(dut, clk_signal="clk_i")
    await tl.reset(rst_signal="rst_ni")
    return tl


@cocotb.test()
async def test_coverage_compare_interrupts(dut):
    """Task 2.2 annotate closure: stimulate comparator and interrupt control paths."""
    tl = await setup(dut)

    await tl.write_reg(ADDR_PRESCALER, 0x3)
    sample_prescaler(0x3)

    await tl.write_reg(ADDR_MTIMECMP0_LOW, 0x20)
    await tl.write_reg(ADDR_MTIMECMP0_HIGH, 0x0)
    sample_compare_programming("cmp0")

    await tl.write_reg(ADDR_MTIMECMP1_LOW, 0x40)
    await tl.write_reg(ADDR_MTIMECMP1_HIGH, 0x0)
    sample_compare_programming("cmp1")

    await tl.write_reg(ADDR_INTR_ENABLE, 0x7)
    sample_intr_enable(0x7)

    # Wait for comparator events to mature.
    for _ in range(320):
        await RisingEdge(dut.clk_i)

    intr_state = await tl.read_reg(ADDR_INTR_STATE)
    assert (intr_state & 0x3) != 0, f"Expected timer interrupt activity, INTR_STATE={intr_state:#010x}"
    if intr_state & 0x1:
        sample_timer_irq_source("timer0")
    if intr_state & 0x2:
        sample_timer_irq_source("timer1")

    # Exercise INTR_TEST write path.
    await tl.write_reg(ADDR_INTR_TEST, 0x2)
    intr_state_after_test = await tl.read_reg(ADDR_INTR_STATE)
    assert (intr_state_after_test & 0x2) == 0x2, (
        f"INTR_TEST bit1 path not observed, INTR_STATE={intr_state_after_test:#010x}"
    )
    sample_timer_irq_source("intr_test")

    # Drive watchdog bark path (without bite) for interrupt source 2.
    await tl.write_reg(ADDR_WATCHDOG_CTRL, 0x1)  # enable, unlocked
    sample_wd_ctrl_value(0x1)

    await tl.write_reg(ADDR_WATCHDOG_BARK_THRESH, 0x00000005)
    await tl.write_reg(ADDR_WATCHDOG_BITE_THRESH, 0x00000100)
    sample_bark_threshold(0x5)
    sample_bite_threshold(0x100)

    for _ in range(40):
        await RisingEdge(dut.clk_i)

    intr_state_bark = await tl.read_reg(ADDR_INTR_STATE)
    assert (intr_state_bark & 0x4) == 0x4, (
        f"Watchdog bark interrupt path not observed, INTR_STATE={intr_state_bark:#010x}"
    )
    sample_timer_irq_source("wd_bark")

    # Pet path under enabled watchdog mode.
    await tl.write_reg(0x28, 0x1)
    sample_pet_event()
