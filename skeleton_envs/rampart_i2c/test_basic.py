"""Skeleton cocotb testbench for rampart_i2c.

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
ADDR_CTRL              = 0x00
ADDR_STATUS            = 0x04
ADDR_RDATA             = 0x08
ADDR_FDATA             = 0x0C
ADDR_FIFO_CTRL         = 0x10
ADDR_FIFO_STATUS       = 0x14
ADDR_OVRD              = 0x18
ADDR_TIMING0           = 0x1C
ADDR_TIMING1           = 0x20
ADDR_TIMING2           = 0x24
ADDR_TIMING3           = 0x28
ADDR_TIMING4           = 0x2C
ADDR_TARGET_ID         = 0x30
ADDR_ACQDATA           = 0x34
ADDR_TXDATA            = 0x38
ADDR_HOST_TIMEOUT_CTRL = 0x3C
ADDR_INTR_STATE        = 0x40
ADDR_INTR_ENABLE       = 0x44
ADDR_INTR_TEST         = 0x48


async def setup(dut):
    """Common test setup: start clock, initialize inputs, assert reset."""
    cocotb.start_soon(Clock(dut.clk_i, 10, units='ns').start())
    dut.scl_i.value = 1  # idle high
    dut.sda_i.value = 1  # idle high
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
    """Verify register reset values after reset."""
    tl = await setup(dut)

    ctrl = await tl.read_reg(ADDR_CTRL)
    assert ctrl == 0, f"CTRL reset mismatch: {ctrl:#010x}"

    # STATUS reset: fmtempty(bit1)=1, txempty(bit3)=1, rxempty(bit5)=1,
    #               host_idle(bit6)=1, target_idle(bit7)=1 => 0xEA
    status = await tl.read_reg(ADDR_STATUS)
    fmtempty = (status >> 1) & 1
    txempty = (status >> 3) & 1
    rxempty = (status >> 5) & 1
    host_idle = (status >> 6) & 1
    target_idle = (status >> 7) & 1
    assert fmtempty == 1, f"FMT FIFO should be empty at reset, STATUS={status:#010x}"
    assert txempty == 1, f"TX FIFO should be empty at reset, STATUS={status:#010x}"
    assert rxempty == 1, f"RX FIFO should be empty at reset, STATUS={status:#010x}"
    assert host_idle == 1, f"Host should be idle at reset, STATUS={status:#010x}"
    assert target_idle == 1, f"Target should be idle at reset, STATUS={status:#010x}"

    intr_state = await tl.read_reg(ADDR_INTR_STATE)
    assert intr_state == 0, f"INTR_STATE reset mismatch: {intr_state:#010x}"

    dut._log.info("test_reset_values PASSED")


@cocotb.test()
async def test_host_enable(dut):
    """Enable host mode and verify status."""
    tl = await setup(dut)

    # Enable host mode (bit 0)
    await tl.write_reg(ADDR_CTRL, 0x1)

    ctrl = await tl.read_reg(ADDR_CTRL)
    assert (ctrl & 0x1) == 1, f"Host enable should be set: CTRL={ctrl:#010x}"

    # Verify host is still idle (no transactions pending)
    for _ in range(5):
        await RisingEdge(dut.clk_i)

    status = await tl.read_reg(ADDR_STATUS)
    host_idle = (status >> 6) & 1
    dut._log.info(f"STATUS after host enable: {status:#010x}, host_idle={host_idle}")

    dut._log.info("test_host_enable PASSED")


@cocotb.test()
async def test_timing_config(dut):
    """Write timing registers and read back to verify."""
    tl = await setup(dut)

    # TIMING0: thigh=0x0050 (bits 15:0), tlow=0x0060 (bits 31:16)
    timing0_val = (0x0060 << 16) | 0x0050
    await tl.write_reg(ADDR_TIMING0, timing0_val)
    readback = await tl.read_reg(ADDR_TIMING0)
    assert readback == timing0_val, f"TIMING0 readback mismatch: {readback:#010x} != {timing0_val:#010x}"

    # TIMING1: t_r=0x0010 (bits 15:0), t_f=0x0010 (bits 31:16)
    timing1_val = (0x0010 << 16) | 0x0010
    await tl.write_reg(ADDR_TIMING1, timing1_val)
    readback = await tl.read_reg(ADDR_TIMING1)
    assert readback == timing1_val, f"TIMING1 readback mismatch: {readback:#010x} != {timing1_val:#010x}"

    # TIMING2: tsu_sta=0x0020, thd_sta=0x0020
    timing2_val = (0x0020 << 16) | 0x0020
    await tl.write_reg(ADDR_TIMING2, timing2_val)
    readback = await tl.read_reg(ADDR_TIMING2)
    assert readback == timing2_val, f"TIMING2 readback mismatch: {readback:#010x} != {timing2_val:#010x}"

    dut._log.info("test_timing_config PASSED")
