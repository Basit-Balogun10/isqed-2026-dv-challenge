"""Skeleton cocotb testbench for citadel_spi.

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
ADDR_CTRL         = 0x00
ADDR_STATUS       = 0x04
ADDR_CONFIGOPTS   = 0x08
ADDR_CSID         = 0x0C
ADDR_COMMAND      = 0x10
ADDR_TXDATA       = 0x14
ADDR_RXDATA       = 0x18
ADDR_ERROR_ENABLE = 0x1C
ADDR_ERROR_STATUS = 0x20
ADDR_INTR_STATE   = 0x24
ADDR_INTR_ENABLE  = 0x28
ADDR_INTR_TEST    = 0x2C


async def setup(dut):
    """Common test setup: start clock, initialize inputs, assert reset."""
    cocotb.start_soon(Clock(dut.clk_i, 10, units='ns').start())
    dut.miso_i.value = 0
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

    # STATUS reset: ready=1(bit0), txempty=1(bit3), rxempty=1(bit9), cmdempty=1(bit15)
    # Expected: 0x00008209
    status = await tl.read_reg(ADDR_STATUS)
    ready = (status >> 0) & 1
    txempty = (status >> 3) & 1
    rxempty = (status >> 9) & 1
    cmdempty = (status >> 15) & 1
    assert ready == 1, f"STATUS.ready should be 1 at reset, STATUS={status:#010x}"
    assert txempty == 1, f"STATUS.txempty should be 1 at reset, STATUS={status:#010x}"
    assert rxempty == 1, f"STATUS.rxempty should be 1 at reset, STATUS={status:#010x}"
    assert cmdempty == 1, f"STATUS.cmdempty should be 1 at reset, STATUS={status:#010x}"

    configopts = await tl.read_reg(ADDR_CONFIGOPTS)
    assert configopts == 0, f"CONFIGOPTS reset mismatch: {configopts:#010x}"

    dut._log.info("test_reset_values PASSED")


@cocotb.test()
async def test_basic_config(dut):
    """Enable SPI host and set clock divider."""
    tl = await setup(dut)

    # Enable SPI (bit 0) and output enable (bit 1)
    await tl.write_reg(ADDR_CTRL, 0x3)

    ctrl = await tl.read_reg(ADDR_CTRL)
    assert ctrl == 0x3, f"CTRL readback mismatch: {ctrl:#010x}"

    # Set CONFIGOPTS: cpol=0, cpha=0, clkdiv=2 (bits 17:2)
    configopts_val = (2 << 2)
    await tl.write_reg(ADDR_CONFIGOPTS, configopts_val)

    readback = await tl.read_reg(ADDR_CONFIGOPTS)
    assert readback == configopts_val, f"CONFIGOPTS readback mismatch: {readback:#010x}"

    # Select chip select 0
    await tl.write_reg(ADDR_CSID, 0)

    dut._log.info("test_basic_config PASSED")


@cocotb.test()
async def test_tx_byte(dut):
    """Write data to TXDATA, issue a TX command, and observe SPI bus activity."""
    tl = await setup(dut)

    # Enable SPI
    await tl.write_reg(ADDR_CTRL, 0x3)

    # Configure: clkdiv=2
    await tl.write_reg(ADDR_CONFIGOPTS, (2 << 2))

    # Write a byte to TX FIFO
    await tl.write_reg(ADDR_TXDATA, 0xAB)

    # Issue command: direction=TX only (0x2), len=0 (1 byte), standard speed
    # direction bits [1:0] = 2 (TX only), len bits [10:2] = 0
    cmd_val = 0x2  # TX direction
    await tl.write_reg(ADDR_COMMAND, cmd_val)

    # Wait for SPI transaction to complete
    for _ in range(200):
        await RisingEdge(dut.clk_i)

    # Check status
    status = await tl.read_reg(ADDR_STATUS)
    dut._log.info(f"STATUS after TX: {status:#010x}")

    dut._log.info("test_tx_byte PASSED")
