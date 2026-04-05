"""Reproduction test for Trace 04 (aegis_aes CBC IV chaining failure)."""

import os
import sys

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from testbench.tl_ul_agent import TlUlDriver

ADDR_KEY_BASE = 0x00
ADDR_IV_BASE = 0x10
ADDR_DATA_IN_BASE = 0x20
ADDR_DATA_OUT_BASE = 0x30
ADDR_CTRL = 0x40
ADDR_TRIGGER = 0x44
ADDR_STATUS = 0x48

NIST_CBC_KEY = 0x2B7E151628AED2A6ABF7158809CF4F3C
NIST_CBC_IV = 0x000102030405060708090A0B0C0D0E0F
NIST_CBC_PT1 = 0x6BC1BEE22E409F96E93D7E117393172A
NIST_CBC_CT1 = 0x7649ABAC8119B246CEE98E9B12E9197D
NIST_CBC_PT2 = 0xAE2D8A571E03AC9C9EB76FAC45AF8E51
NIST_CBC_CT2 = 0x5086CB9B507219EE95DB113A917678B2


async def setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    tl = TlUlDriver(dut, clk_signal="clk_i")
    await tl.reset(rst_signal="rst_ni")
    return tl


async def write_128(tl, base_addr, value):
    for index in range(4):
        word = (value >> (32 * (3 - index))) & 0xFFFFFFFF
        await tl.write_reg(base_addr + (index * 4), word)


async def read_128(tl, base_addr):
    result = 0
    for index in range(4):
        word = await tl.read_reg(base_addr + (index * 4))
        result = (result << 32) | (word & 0xFFFFFFFF)
    return result


async def wait_output_valid(tl, max_polls=1200):
    for _ in range(max_polls):
        status = await tl.read_reg(ADDR_STATUS)
        if status & 0x2:
            return
    raise AssertionError("Timed out waiting for AES output_valid in STATUS[1]")


@cocotb.test()
async def test_repro_04(dut):
    """Fail if CBC block N+1 does not use ciphertext C[N] as IV."""
    tl = await setup(dut)

    # Program key + IV and run block 0.
    await write_128(tl, ADDR_KEY_BASE, NIST_CBC_KEY)
    await write_128(tl, ADDR_IV_BASE, NIST_CBC_IV)
    await write_128(tl, ADDR_DATA_IN_BASE, NIST_CBC_PT1)
    await tl.write_reg(ADDR_CTRL, 0x1)      # CBC encrypt
    await tl.write_reg(ADDR_TRIGGER, 0x1)   # start

    await wait_output_valid(tl)
    c0 = await read_128(tl, ADDR_DATA_OUT_BASE)
    iv_after_block0 = await read_128(tl, ADDR_IV_BASE)

    assert c0 == NIST_CBC_CT1, (
        f"Unexpected C0 value while reproducing Trace-04: got {c0:#034x}, "
        f"expected {NIST_CBC_CT1:#034x}"
    )

    assert iv_after_block0 == c0, (
        "Trace-04 bug reproduced: CBC IV register was not updated with C0 after block 0 "
        f"(iv_after_block0={iv_after_block0:#034x}, c0={c0:#034x})"
    )

    # Block 1 must use updated IV (= C0).
    await write_128(tl, ADDR_DATA_IN_BASE, NIST_CBC_PT2)
    await tl.write_reg(ADDR_TRIGGER, 0x1)

    await wait_output_valid(tl)
    c1 = await read_128(tl, ADDR_DATA_OUT_BASE)

    assert c1 == NIST_CBC_CT2, (
        "Trace-04 bug reproduced: block1 CBC ciphertext mismatch, likely due to stale IV "
        f"(got {c1:#034x}, expected {NIST_CBC_CT2:#034x})"
    )
