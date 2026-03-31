"""Skeleton cocotb testbench for bastion_gpio.

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
ADDR_DATA_IN              = 0x00
ADDR_DATA_OUT             = 0x04
ADDR_DIR                  = 0x08
ADDR_INTR_STATE           = 0x0C
ADDR_INTR_ENABLE          = 0x10
ADDR_INTR_TEST            = 0x14
ADDR_INTR_CTRL_EN_RISING  = 0x18
ADDR_INTR_CTRL_EN_FALLING = 0x1C
ADDR_INTR_CTRL_EN_LVLHIGH = 0x20
ADDR_INTR_CTRL_EN_LVLLOW  = 0x24
ADDR_MASKED_OUT_LOWER     = 0x28
ADDR_MASKED_OUT_UPPER     = 0x2C


async def setup(dut):
    """Common test setup: start clock, initialize inputs, assert reset."""
    cocotb.start_soon(Clock(dut.clk_i, 10, units='ns').start())
    dut.gpio_i.value = 0
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
    """Verify all registers are at their reset values."""
    tl = await setup(dut)

    data_in = await tl.read_reg(ADDR_DATA_IN)
    assert data_in == 0, f"DATA_IN reset mismatch: {data_in:#010x}"

    data_out = await tl.read_reg(ADDR_DATA_OUT)
    assert data_out == 0, f"DATA_OUT reset mismatch: {data_out:#010x}"

    dir_val = await tl.read_reg(ADDR_DIR)
    assert dir_val == 0, f"DIR reset mismatch: {dir_val:#010x}"

    intr_state = await tl.read_reg(ADDR_INTR_STATE)
    assert intr_state == 0, f"INTR_STATE reset mismatch: {intr_state:#010x}"

    intr_en = await tl.read_reg(ADDR_INTR_ENABLE)
    assert intr_en == 0, f"INTR_ENABLE reset mismatch: {intr_en:#010x}"

    dut._log.info("test_reset_values PASSED")


@cocotb.test()
async def test_output_direction(dut):
    """Set direction to output, write DATA_OUT, verify gpio_o reflects the value."""
    tl = await setup(dut)

    # Set pins [7:0] as outputs
    await tl.write_reg(ADDR_DIR, 0x000000FF)

    # Write a pattern to DATA_OUT
    await tl.write_reg(ADDR_DATA_OUT, 0x000000A5)

    # Wait a couple of cycles for output to propagate
    for _ in range(3):
        await RisingEdge(dut.clk_i)

    gpio_out = int(dut.gpio_o.value)
    dut._log.info(f"gpio_o = {gpio_out:#010x}")
    assert (gpio_out & 0xFF) == 0xA5, f"gpio_o mismatch: {gpio_out:#010x}"

    dut._log.info("test_output_direction PASSED")


@cocotb.test()
async def test_input_read(dut):
    """Drive gpio_i externally and verify DATA_IN register reflects the value."""
    tl = await setup(dut)

    # Drive input pins
    dut.gpio_i.value = 0xDEADBEEF

    # Wait for synchronizer (typically 2-3 cycles)
    for _ in range(5):
        await RisingEdge(dut.clk_i)

    data_in = await tl.read_reg(ADDR_DATA_IN)
    dut._log.info(f"DATA_IN = {data_in:#010x}")
    assert data_in == 0xDEADBEEF, f"DATA_IN mismatch: got {data_in:#010x}, expected 0xDEADBEEF"

    dut._log.info("test_input_read PASSED")
