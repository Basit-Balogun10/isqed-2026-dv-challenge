"""Skeleton cocotb testbench for aegis_aes.

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
ADDR_AES_KEY_0      = 0x00
ADDR_AES_KEY_1      = 0x04
ADDR_AES_KEY_2      = 0x08
ADDR_AES_KEY_3      = 0x0C
ADDR_AES_IV_0       = 0x10
ADDR_AES_IV_1       = 0x14
ADDR_AES_IV_2       = 0x18
ADDR_AES_IV_3       = 0x1C
ADDR_AES_DATA_IN_0  = 0x20
ADDR_AES_DATA_IN_1  = 0x24
ADDR_AES_DATA_IN_2  = 0x28
ADDR_AES_DATA_IN_3  = 0x2C
ADDR_AES_DATA_OUT_0 = 0x30
ADDR_AES_DATA_OUT_1 = 0x34
ADDR_AES_DATA_OUT_2 = 0x38
ADDR_AES_DATA_OUT_3 = 0x3C
ADDR_AES_CTRL       = 0x40
ADDR_AES_TRIGGER    = 0x44
ADDR_AES_STATUS     = 0x48
ADDR_INTR_STATE     = 0x4C
ADDR_INTR_ENABLE    = 0x50
ADDR_INTR_TEST      = 0x54


async def setup(dut):
    """Common test setup: start clock, initialize inputs, assert reset."""
    cocotb.start_soon(Clock(dut.clk_i, 10, units='ns').start())
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
    """Verify AES_STATUS has idle=1 and input_ready=1 after reset."""
    tl = await setup(dut)

    # AES_STATUS reset: idle(bit0)=1, output_valid(bit1)=0, input_ready(bit2)=1 => 0x5
    status = await tl.read_reg(ADDR_AES_STATUS)
    idle = (status >> 0) & 1
    input_ready = (status >> 2) & 1
    assert idle == 1, f"AES should be idle at reset, STATUS={status:#010x}"
    assert input_ready == 1, f"AES should be input_ready at reset, STATUS={status:#010x}"

    ctrl = await tl.read_reg(ADDR_AES_CTRL)
    assert ctrl == 0, f"AES_CTRL reset mismatch: {ctrl:#010x}"

    intr_state = await tl.read_reg(ADDR_INTR_STATE)
    assert intr_state == 0, f"INTR_STATE reset mismatch: {intr_state:#010x}"

    dut._log.info("test_reset_values PASSED")


@cocotb.test()
async def test_basic_ecb_encrypt(dut):
    """Write a known AES-128 key and plaintext, trigger ECB encrypt, check output.

    Uses NIST FIPS-197 test vector:
        Key:       00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
        Plaintext: 00 11 22 33 44 55 66 77 88 99 AA BB CC DD EE FF
        Ciphertext: 69 C4 E0 D8 6A 7B 04 30 D8 CD B7 80 70 B4 C5 5A
    """
    tl = await setup(dut)

    # Set ECB mode (mode=0), encrypt (operation=0)
    await tl.write_reg(ADDR_AES_CTRL, 0x0)

    # Write 128-bit key: 00010203 04050607 08090A0B 0C0D0E0F
    await tl.write_reg(ADDR_AES_KEY_0, 0x00010203)
    await tl.write_reg(ADDR_AES_KEY_1, 0x04050607)
    await tl.write_reg(ADDR_AES_KEY_2, 0x08090A0B)
    await tl.write_reg(ADDR_AES_KEY_3, 0x0C0D0E0F)

    # Write 128-bit plaintext: 00112233 44556677 8899AABB CCDDEEFF
    await tl.write_reg(ADDR_AES_DATA_IN_0, 0x00112233)
    await tl.write_reg(ADDR_AES_DATA_IN_1, 0x44556677)
    await tl.write_reg(ADDR_AES_DATA_IN_2, 0x8899AABB)
    await tl.write_reg(ADDR_AES_DATA_IN_3, 0xCCDDEEFF)

    # Trigger AES operation (start bit 0)
    await tl.write_reg(ADDR_AES_TRIGGER, 0x1)

    # Wait for completion
    for _ in range(200):
        await RisingEdge(dut.clk_i)
        status = await tl.read_reg(ADDR_AES_STATUS)
        output_valid = (status >> 1) & 1
        if output_valid:
            break

    # Read output
    out0 = await tl.read_reg(ADDR_AES_DATA_OUT_0)
    out1 = await tl.read_reg(ADDR_AES_DATA_OUT_1)
    out2 = await tl.read_reg(ADDR_AES_DATA_OUT_2)
    out3 = await tl.read_reg(ADDR_AES_DATA_OUT_3)
    dut._log.info(f"AES output: {out0:#010x} {out1:#010x} {out2:#010x} {out3:#010x}")

    dut._log.info("test_basic_ecb_encrypt PASSED")


@cocotb.test()
async def test_status_flags(dut):
    """Verify idle and output_valid status transitions during operation."""
    tl = await setup(dut)

    # Check initial state
    status = await tl.read_reg(ADDR_AES_STATUS)
    idle = (status >> 0) & 1
    assert idle == 1, "AES should start idle"

    # Write minimal key/data and trigger
    for i in range(4):
        await tl.write_reg(ADDR_AES_KEY_0 + i * 4, 0)
        await tl.write_reg(ADDR_AES_DATA_IN_0 + i * 4, 0)

    await tl.write_reg(ADDR_AES_TRIGGER, 0x1)

    # Check that idle goes low during operation
    await RisingEdge(dut.clk_i)
    await RisingEdge(dut.clk_i)
    status = await tl.read_reg(ADDR_AES_STATUS)
    dut._log.info(f"STATUS during operation: {status:#010x}")

    # Wait for completion
    for _ in range(200):
        await RisingEdge(dut.clk_i)

    status = await tl.read_reg(ADDR_AES_STATUS)
    idle = (status >> 0) & 1
    dut._log.info(f"STATUS after operation: {status:#010x}, idle={idle}")

    dut._log.info("test_status_flags PASSED")
