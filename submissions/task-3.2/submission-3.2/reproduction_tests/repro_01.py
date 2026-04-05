"""Reproduction test for Trace 01 (warden_timer split-write spurious interrupt)."""

import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from testbench.tl_ul_agent import TlUlDriver

ADDR_MTIME_LOW = 0x00
ADDR_MTIMECMP0_LOW = 0x08
ADDR_MTIMECMP0_HIGH = 0x0C
ADDR_PRESCALER = 0x18
ADDR_INTR_STATE = 0x30
ADDR_INTR_ENABLE = 0x34


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    tl = TlUlDriver(dut, clk_signal="clk_i")
    await tl.reset(rst_signal="rst_ni")
    return tl


@cocotb.test()
async def test_repro_01(dut):
    """Fail if timer interrupt asserts during a split MTIMECMP0 write."""
    tl = await setup(dut)

    # Fast-running timer and enabled interrupt path.
    await tl.write_reg(ADDR_PRESCALER, 0x0)
    await tl.write_reg(ADDR_INTR_ENABLE, 0x1)

    # Clear reset-time pending interrupt state caused by mtimecmp reset value.
    await tl.write_reg(ADDR_INTR_STATE, 0x1)

    # Wait until mtime has advanced beyond the low-half target (0x50).
    reached_window = False
    for _ in range(400):
        mtime_low = await tl.read_reg(ADDR_MTIME_LOW)
        if mtime_low >= 0x90:
            reached_window = True
            break
        await RisingEdge(dut.clk_i)
    assert reached_window, "Timeout waiting for mtime to reach split-write stress window"

    # Split write: low-half first, then high-half (classic TOCTOU hazard).
    await tl.write_reg(ADDR_MTIMECMP0_LOW, 0x00000050)

    for _ in range(4):
        await RisingEdge(dut.clk_i)

    intr_state_mid = await tl.read_reg(ADDR_INTR_STATE)
    assert (intr_state_mid & 0x1) == 0, (
        "Trace-01 bug reproduced: INTR_STATE[0] asserted after LOW-half write while "
        "HIGH-half was still stale"
    )

    await tl.write_reg(ADDR_MTIMECMP0_HIGH, 0x00000001)

    for _ in range(32):
        await RisingEdge(dut.clk_i)

    intr_state_after = await tl.read_reg(ADDR_INTR_STATE)
    assert (intr_state_after & 0x1) == 0, (
        "Trace-01 bug reproduced: timer0 interrupt asserted before mtime reached "
        "full 64-bit compare value"
    )
