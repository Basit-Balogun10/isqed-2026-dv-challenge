# mypy: disable-error-code=import-not-found
"""VP-AES-005: Key expansion with various patterns. Priority: high"""

import cocotb
from cocotb.triggers import Timer, RisingEdge
from .helpers import generate_clock, generate_reset


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
async def test_vp_aes_005(dut):
    """VP-AES-005: Test key expansion with all-zero key"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    zero_key = 0x00000000000000000000000000000000
    zero_pt = 0x00000000000000000000000000000000
    await write_aes_128(dut, 0x00, zero_key)
    await write_aes_128(dut, 0x20, zero_pt)
    await write_aes_csr(dut, 0x40, 0x0)
    await write_aes_csr(dut, 0x44, 0x1)
    for _ in range(10000):
        status = await read_aes_csr(dut, 0x48)
        if (status & 0x2) != 0:
            break
        await Timer(10, unit="ns")
    ct = await read_aes_128(dut, 0x30)
    assert ct != 0, "All-zero key must produce non-zero ciphertext"
    cocotb.log.info(f"[VP-AES-005] ✓ PASS: {ct:#034x}")
