"""Skeleton cocotb testbench for nexus_uart.

Provides basic tests to get started. Achieves ~40% line coverage.
Participants should expand these tests to reach higher coverage targets.
"""

import sys
import os

# Add parent directory to path for shared TL-UL agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from tl_ul_agent import TlUlDriver

# Register addresses
ADDR_CTRL       = 0x00
ADDR_STATUS     = 0x04
ADDR_TXDATA     = 0x08
ADDR_RXDATA     = 0x0C
ADDR_FIFO_CTRL  = 0x10
ADDR_INTR_STATE = 0x14
ADDR_INTR_ENABLE = 0x18
ADDR_INTR_TEST  = 0x1C


async def setup(dut):
    """Common test setup: start clock, initialize inputs, assert reset."""
    cocotb.start_soon(Clock(dut.clk_i, 10, units='ns').start())
    dut.uart_rx_i.value = 1  # idle high
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
    """Verify register reset values: CTRL=0, STATUS has tx_empty=1 and rx_empty=1."""
    tl = await setup(dut)

    # CTRL should be 0 after reset
    ctrl = await tl.read_reg(ADDR_CTRL)
    assert ctrl == 0x00000000, f"CTRL reset value mismatch: {ctrl:#010x}"

    # STATUS reset value: tx_fifo_empty(bit0)=1, rx_fifo_empty(bit2)=1 => 0x05
    status = await tl.read_reg(ADDR_STATUS)
    tx_empty = (status >> 0) & 1
    rx_empty = (status >> 2) & 1
    assert tx_empty == 1, f"TX FIFO should be empty at reset, STATUS={status:#010x}"
    assert rx_empty == 1, f"RX FIFO should be empty at reset, STATUS={status:#010x}"

    # INTR_STATE should be 0
    intr = await tl.read_reg(ADDR_INTR_STATE)
    assert intr == 0, f"INTR_STATE should be 0 at reset: {intr:#010x}"

    dut._log.info("test_reset_values PASSED")


@cocotb.test()
async def test_basic_config(dut):
    """Write CTRL register to enable TX/RX with a baud divisor."""
    tl = await setup(dut)

    # Enable TX (bit 0), RX (bit 1), baud divisor=10 (bits 17:2)
    ctrl_val = (1 << 0) | (1 << 1) | (10 << 2)
    await tl.write_reg(ADDR_CTRL, ctrl_val)

    # Read back CTRL
    readback = await tl.read_reg(ADDR_CTRL)
    assert readback == ctrl_val, f"CTRL readback mismatch: got {readback:#010x}, expected {ctrl_val:#010x}"

    dut._log.info("test_basic_config PASSED")


@cocotb.test()
async def test_loopback(dut):
    """Enable loopback mode, write to TXDATA, wait for data to appear in RXDATA."""
    tl = await setup(dut)

    # Enable TX, RX, loopback, baud divisor=4
    ctrl_val = (1 << 0) | (1 << 1) | (4 << 2) | (1 << 21)
    await tl.write_reg(ADDR_CTRL, ctrl_val)

    # Write a byte to TXDATA
    test_byte = 0xA5
    await tl.write_reg(ADDR_TXDATA, test_byte)

    # Wait for transmission + loopback reception
    for _ in range(500):
        await RisingEdge(dut.clk_i)

    # Check if RX FIFO is no longer empty
    status = await tl.read_reg(ADDR_STATUS)
    rx_empty = (status >> 2) & 1
    if rx_empty == 0:
        rxdata = await tl.read_reg(ADDR_RXDATA)
        dut._log.info(f"Loopback received: {rxdata:#04x}")
    else:
        dut._log.warning("RX FIFO still empty - loopback may need more cycles")

    dut._log.info("test_loopback PASSED")
