"""Reproduction test for Trace 05 (rampart_i2c repeated START emits STOP)."""

import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from testbench.tl_ul_agent import TlUlDriver

ADDR_CTRL = 0x00
ADDR_FDATA = 0x0C
ADDR_TIMING0 = 0x1C
ADDR_TIMING2 = 0x24

HOST_ENABLE = 1 << 0
LINE_LOOPBACK = 1 << 2


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    dut.scl_i.value = 1
    dut.sda_i.value = 1
    tl = TlUlDriver(dut, clk_signal="clk_i")
    await tl.reset(rst_signal="rst_ni")
    return tl


@cocotb.test()
async def test_repro_05(dut):
    """Fail if stop_det pulses between first START and repeated START."""
    tl = await setup(dut)

    # Host mode with internal line loopback for deterministic bus observation.
    await tl.write_reg(ADDR_CTRL, HOST_ENABLE | LINE_LOOPBACK)

    # Match trace timing intent: tlow/thigh=50, tsu_sta/thd_sta=10.
    await tl.write_reg(ADDR_TIMING0, (50 << 16) | 50)
    await tl.write_reg(ADDR_TIMING2, (10 << 16) | 10)

    # FDATA format: [12]=nakok, [11]=rcont, [10]=readb, [9]=stop, [8]=start, [7:0]=byte
    # Command sequence: START+ADDR(W), DATA, REPEATED_START+ADDR(R), READ1+STOP.
    cmd_start_addr_w = (1 << 12) | (1 << 8) | 0xA0
    cmd_write_data = (1 << 12) | 0xAA
    cmd_rstart_addr_r = (1 << 12) | (1 << 8) | 0xA1
    cmd_read_one_stop = (1 << 10) | (1 << 9) | 0x01

    await tl.write_reg(ADDR_FDATA, cmd_start_addr_w)
    await tl.write_reg(ADDR_FDATA, cmd_write_data)
    await tl.write_reg(ADDR_FDATA, cmd_rstart_addr_r)
    await tl.write_reg(ADDR_FDATA, cmd_read_one_stop)

    start_count = 0
    stop_between_starts = False

    for _ in range(4000):
        await RisingEdge(dut.clk_i)

        start_det = int(dut.start_det.value)
        stop_det = int(dut.stop_det.value)

        if start_det:
            start_count += 1
            if start_count >= 2:
                break

        if start_count == 1 and stop_det:
            stop_between_starts = True

    assert (
        start_count >= 2
    ), "Did not observe two START events; repeated-START stimulus did not execute correctly"

    assert (
        not stop_between_starts
    ), "Trace-05 bug reproduced: STOP condition detected between first START and repeated START"
