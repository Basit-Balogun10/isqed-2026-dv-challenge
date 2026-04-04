# mypy: disable-error-code=import-not-found
"""
VP-AES-003: CBC encrypt test vector

Load NIST SP 800-38A CBC encrypt test vector (key, IV, plaintext).
Set mode=CBC, operation=encrypt, and verify ciphertext matches known-answer.

Priority: high
Coverage Target: cp_mode.cbc cross cp_op.encrypt cross cp_kat
"""

import cocotb
from cocotb.triggers import Timer, RisingEdge
from .helpers import generate_clock, generate_reset

NIST_CBC_KEY = 0x2B7E151628AED2A6ABF7158809CF4F3C
NIST_CBC_IV = 0x000102030405060708090A0B0C0D0E0F
NIST_CBC_PT1 = 0x6BC1BEE22E409F96E93D7E117393172A
NIST_CBC_CT1 = 0x7649ABAC8119B246CEE98E9B12E9197D


async def write_aes_csr(dut, addr, data):
    dut.tl_a_valid_i.value = 1
    dut.tl_a_opcode_i.value = 0
    dut.tl_a_address_i.value = addr
    dut.tl_a_data_i.value = data
    dut.tl_a_mask_i.value = 0xF
    dut.tl_a_size_i.value = 2
    dut.tl_d_ready_i.value = 1
    await RisingEdge(dut.clk_i)
    for _ in range(20):
        if int(dut.tl_a_ready_o.value) == 1:
            break
        await RisingEdge(dut.clk_i)
    dut.tl_a_valid_i.value = 0


async def read_aes_csr(dut, addr):
    dut.tl_a_valid_i.value = 1
    dut.tl_a_opcode_i.value = 4
    dut.tl_a_address_i.value = addr
    dut.tl_a_size_i.value = 2
    dut.tl_d_ready_i.value = 1
    await RisingEdge(dut.clk_i)
    for _ in range(20):
        if int(dut.tl_a_ready_o.value) == 1:
            break
        await RisingEdge(dut.clk_i)
    dut.tl_a_valid_i.value = 0
    for _ in range(100):
        if int(dut.tl_d_valid_o.value) == 1:
            result = int(dut.tl_d_data_o.value)
            await RisingEdge(dut.clk_i)
            return result
        await RisingEdge(dut.clk_i)
    return 0


async def write_aes_128(dut, start_addr, value):
    for i in range(4):
        word = (value >> (32 * (3 - i))) & 0xFFFFFFFF
        await write_aes_csr(dut, start_addr + (i * 4), word)
        await Timer(20, unit="ns")


async def read_aes_128(dut, start_addr):
    result = 0
    for i in range(4):
        word = await read_aes_csr(dut, start_addr + (i * 4))
        result = (result << 32) | word
        await Timer(10, unit="ns")
    return result


@cocotb.test()
async def test_vp_aes_003(dut):
    """VP-AES-003: CBC encrypt NIST test vector"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info(f"[VP-AES-003] Starting CBC encrypt test")

    await write_aes_128(dut, 0x00, NIST_CBC_KEY)
    await write_aes_128(dut, 0x10, NIST_CBC_IV)
    await write_aes_128(dut, 0x20, NIST_CBC_PT1)
    await write_aes_csr(dut, 0x40, 0x1)  # mode=CBC, op=encrypt
    await write_aes_csr(dut, 0x44, 0x1)

    for _ in range(10000):
        status = await read_aes_csr(dut, 0x48)
        if (status & 0x2) != 0:
            break
        await Timer(10, unit="ns")

    ct = await read_aes_128(dut, 0x30)
    cocotb.log.info(f"  Got:      {ct:#034x}")
    cocotb.log.info(f"  Expected: {NIST_CBC_CT1:#034x}")

    assert (
        ct == NIST_CBC_CT1
    ), f"CBC encrypt mismatch: {ct:#034x} != {NIST_CBC_CT1:#034x}"
    cocotb.log.info(f"[VP-AES-003] ✓ PASS")
