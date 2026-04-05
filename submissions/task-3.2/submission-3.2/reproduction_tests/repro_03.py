"""Reproduction test for Trace 03 (citadel_spi CS hold-time violation)."""

import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from testbench.tl_ul_agent import TlUlDriver

ADDR_CTRL = 0x00
ADDR_CONFIGOPTS = 0x08
ADDR_CSID = 0x0C
ADDR_COMMAND = 0x10
ADDR_TXDATA = 0x14

FSM_CS_HOLD = 3


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    dut.miso_i.value = 0
    tl = TlUlDriver(dut, clk_signal="clk_i")
    await tl.reset(rst_signal="rst_ni")
    return tl


@cocotb.test()
async def test_repro_03(dut):
    """Fail if CSn deasserts before csn_trail SCLK periods elapse."""
    tl = await setup(dut)

    # Enable SPI and output.
    await tl.write_reg(ADDR_CTRL, 0x3)
    await tl.write_reg(ADDR_CSID, 0x0)

    # CONFIGOPTS: clkdiv=4, csn_lead=2, csn_trail=4, csn_idle=3, cpol/cpha=0.
    configopts = (4 << 0) | (2 << 16) | (4 << 20) | (3 << 24)
    await tl.write_reg(ADDR_CONFIGOPTS, configopts)

    # One-byte transfer.
    await tl.write_reg(ADDR_TXDATA, 0xA5)
    await tl.write_reg(ADDR_COMMAND, 0x00000000)  # dir=TX, len=0 -> single byte

    seen_hold = False
    hold_ticks = 0

    for _ in range(3500):
        await RisingEdge(dut.clk_i)
        state = int(dut.fsm_state.value)
        csn0 = int(dut.csn_o.value) & 0x1
        clk_div_tick = int(dut.clk_div_tick.value)

        if state == FSM_CS_HOLD and csn0 == 0:
            seen_hold = True
            if clk_div_tick:
                hold_ticks += 1

        if seen_hold and csn0 == 1:
            break

    assert seen_hold, "Did not observe SPI FSM entering CS_HOLD phase"
    assert hold_ticks >= 4, (
        "Trace-03 bug reproduced: CS hold time shorter than configured csn_trail "
        f"(expected >=4 SCLK ticks, observed {hold_ticks})"
    )
