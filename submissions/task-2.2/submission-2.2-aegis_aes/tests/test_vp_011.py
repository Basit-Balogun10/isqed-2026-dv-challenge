# mypy: disable-error-code=import-not-found
"""VP-AES-011: Read DATA_OUT before output_valid. Priority: medium"""

import cocotb
from cocotb.triggers import Timer, RisingEdge
from .helpers import generate_clock, generate_reset


async def csr_write(dut, addr, data):
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


async def csr_read(dut, addr):
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


async def write_128(dut, addr, val):
    for i in range(4):
        w = (val >> (32 * (3 - i))) & 0xFFFFFFFF
        await csr_write(dut, addr + (i * 4), w)
        await Timer(20, unit="ns")


async def read_128(dut, addr):
    r = 0
    for i in range(4):
        w = await csr_read(dut, addr + (i * 4))
        r = (r << 32) | w
        await Timer(10, unit="ns")
    return r


@cocotb.test()
async def test_vp_aes_011(dut):
    """VP-AES-011: Read before output_valid - may get stale data"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    key = 0x2B7E151628AED2A6ABF7158809CF4F3C
    pt = 0x11111111111111111111111111111111
    await write_128(dut, 0x00, key)
    await write_128(dut, 0x20, pt)
    await csr_write(dut, 0x40, 0x0)
    await csr_write(dut, 0x44, 0x1)
    await Timer(100, unit="ns")
    stale = await read_128(dut, 0x30)
    for _ in range(10000):
        if (await csr_read(dut, 0x48) & 0x2) != 0:
            break
        await Timer(10, unit="ns")
    status = await csr_read(dut, 0x48)
    assert (status & 0x2) != 0, "output_valid bit never asserted"
    valid = await read_128(dut, 0x30)
    assert valid != 0, "Valid DATA_OUT should not remain all-zero after encryption"
    cocotb.log.info(f"[VP-AES-011] Stale: {stale:#034x}, Valid: {valid:#034x} ✓ PASS")
