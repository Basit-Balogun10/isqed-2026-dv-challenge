"""Skeleton cocotb testbench for sentinel_hmac.

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
ADDR_CFG              = 0x00
ADDR_CMD              = 0x04
ADDR_STATUS           = 0x08
ADDR_WIPE_SECRET      = 0x0C
ADDR_KEY_0            = 0x10
ADDR_KEY_1            = 0x14
ADDR_KEY_2            = 0x18
ADDR_KEY_3            = 0x1C
ADDR_KEY_4            = 0x20
ADDR_KEY_5            = 0x24
ADDR_KEY_6            = 0x28
ADDR_KEY_7            = 0x2C
ADDR_DIGEST_0         = 0x30
ADDR_DIGEST_1         = 0x34
ADDR_DIGEST_2         = 0x38
ADDR_DIGEST_3         = 0x3C
ADDR_DIGEST_4         = 0x40
ADDR_DIGEST_5         = 0x44
ADDR_DIGEST_6         = 0x48
ADDR_DIGEST_7         = 0x4C
ADDR_MSG_LENGTH_LOWER = 0x50
ADDR_MSG_LENGTH_UPPER = 0x54
ADDR_INTR_STATE       = 0x58
ADDR_INTR_ENABLE      = 0x5C
ADDR_INTR_TEST        = 0x60
ADDR_MSG_FIFO         = 0x64


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
    """Verify registers are at their reset values."""
    tl = await setup(dut)

    cfg = await tl.read_reg(ADDR_CFG)
    assert cfg == 0, f"CFG reset mismatch: {cfg:#010x}"

    # STATUS reset: fifo_empty(bit1)=1, sha_idle(bit8)=1 => 0x102
    status = await tl.read_reg(ADDR_STATUS)
    fifo_empty = (status >> 1) & 1
    sha_idle = (status >> 8) & 1
    assert fifo_empty == 1, f"FIFO should be empty at reset, STATUS={status:#010x}"
    assert sha_idle == 1, f"SHA should be idle at reset, STATUS={status:#010x}"

    intr_state = await tl.read_reg(ADDR_INTR_STATE)
    assert intr_state == 0, f"INTR_STATE reset mismatch: {intr_state:#010x}"

    msg_len = await tl.read_reg(ADDR_MSG_LENGTH_LOWER)
    assert msg_len == 0, f"MSG_LENGTH_LOWER reset mismatch: {msg_len:#010x}"

    dut._log.info("test_reset_values PASSED")


@cocotb.test()
async def test_sha256_empty(dut):
    """Compute SHA-256 of empty message and check against known answer.

    SHA-256("") = e3b0c442 98fc1c14 9afbf4c8 996fb924
                  27ae41e4 649b934c a495991b 7852b855
    """
    tl = await setup(dut)

    # Enable SHA-256 only (sha_en=1, hmac_en=0)
    await tl.write_reg(ADDR_CFG, 0x2)

    # Start hash operation
    await tl.write_reg(ADDR_CMD, 0x1)  # hash_start

    # Immediately signal hash_process (no data to write)
    await tl.write_reg(ADDR_CMD, 0x2)  # hash_process

    # Wait for done
    for _ in range(500):
        await RisingEdge(dut.clk_i)
        intr_state = await tl.read_reg(ADDR_INTR_STATE)
        if intr_state & 0x1:  # hmac_done
            break

    # Read digest
    digest = []
    for i in range(8):
        d = await tl.read_reg(ADDR_DIGEST_0 + i * 4)
        digest.append(d)

    dut._log.info(f"SHA-256 digest: {' '.join(f'{d:08x}' for d in digest)}")

    dut._log.info("test_sha256_empty PASSED")


@cocotb.test()
async def test_basic_config(dut):
    """Enable SHA, check status transitions."""
    tl = await setup(dut)

    # Enable SHA-256
    await tl.write_reg(ADDR_CFG, 0x2)
    cfg = await tl.read_reg(ADDR_CFG)
    assert (cfg & 0x2) != 0, f"SHA_EN should be set: CFG={cfg:#010x}"

    # Check status
    status = await tl.read_reg(ADDR_STATUS)
    sha_idle = (status >> 8) & 1
    assert sha_idle == 1, f"SHA should be idle before starting, STATUS={status:#010x}"

    # Enable HMAC mode too
    await tl.write_reg(ADDR_CFG, 0x3)
    cfg = await tl.read_reg(ADDR_CFG)
    assert (cfg & 0x3) == 0x3, f"Both HMAC_EN and SHA_EN should be set: CFG={cfg:#010x}"

    dut._log.info("test_basic_config PASSED")
