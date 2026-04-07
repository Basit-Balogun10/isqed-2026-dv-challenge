"""Reproduction test for Trace 02 (nexus_uart TX FIFO overflow corruption)."""

import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from testbench.tl_ul_agent import TlUlDriver

ADDR_CTRL = 0x00
ADDR_STATUS = 0x04
ADDR_TXDATA = 0x08


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    dut.uart_rx_i.value = 1
    tl = TlUlDriver(dut, clk_signal="clk_i")
    await tl.reset(rst_signal="rst_ni")
    return tl


@cocotb.test()
async def test_repro_02(dut):
    """Fail if overflow writes corrupt FIFO entry 0 while FIFO is full."""
    tl = await setup(dut)

    # Enable TX/RX with a small divisor so TX state machine is live.
    ctrl_val = (1 << 0) | (1 << 1) | (4 << 2)
    await tl.write_reg(ADDR_CTRL, ctrl_val)

    # Fill FIFO with deterministic data 0x00..0x1F.
    for byte_val in range(32):
        await tl.write_reg(ADDR_TXDATA, byte_val)

    status_full = await tl.read_reg(ADDR_STATUS)
    tx_fifo_full = (status_full >> 1) & 0x1
    assert (
        tx_fifo_full == 1
    ), f"Precondition failed: TX FIFO not full, STATUS={status_full:#010x}"

    # Overflow attempts (should be discarded without touching stored contents).
    await tl.write_reg(ADDR_TXDATA, 0x80)
    await tl.write_reg(ADDR_TXDATA, 0x81)
    await tl.write_reg(ADDR_TXDATA, 0x82)

    await RisingEdge(dut.clk_i)

    # In a correct design, FIFO head stays 0x00 and write pointer does not advance.
    fifo_head = int(dut.tx_fifo_rdata.value) & 0xFF
    tx_wptr = int(dut.tx_wptr.value)

    assert (
        tx_wptr == 0x20
    ), f"Trace-02 bug reproduced: tx_wptr advanced on overflow, expected 0x20 got {tx_wptr:#x}"
    assert fifo_head == 0x00, (
        "Trace-02 bug reproduced: TX FIFO head corrupted during overflow write "
        f"(expected 0x00, observed {fifo_head:#04x})"
    )
