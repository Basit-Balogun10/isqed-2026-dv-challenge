# mypy: disable-error-code=import-not-found
"""VP-AES-006: Back-to-back ECB operations. Priority: high"""

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
async def test_vp_aes_006(dut):
    """VP-AES-006: Back-to-back ECB encrypt operations"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    key = 0x2B7E151628AED2A6ABF7158809CF4F3C
    await write_aes_128(dut, 0x00, key)
    await write_aes_csr(dut, 0x40, 0x0)

    # Operation 1
    await write_aes_128(dut, 0x20, 0x11111111111111111111111111111111)
    await write_aes_csr(dut, 0x44, 0x1)
    for _ in range(10000):
        if (await read_aes_csr(dut, 0x48) & 0x2) != 0:
            break
        await Timer(10, unit="ns")
    ct1 = await read_aes_128(dut, 0x30)

    # Operation 2
    await write_aes_128(dut, 0x20, 0x22222222222222222222222222222222)
    await write_aes_csr(dut, 0x44, 0x1)
    for _ in range(10000):
        if (await read_aes_csr(dut, 0x48) & 0x2) != 0:
            break
        await Timer(10, unit="ns")
    ct2 = await read_aes_128(dut, 0x30)

    assert ct1 != ct2, "Back-to-back operations should produce different outputs"
    cocotb.log.info(f"[VP-AES-006] ✓ PASS")
