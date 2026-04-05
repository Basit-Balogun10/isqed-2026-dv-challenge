# mypy: disable-error-code=import-not-found
"""
VP-AES-001: NIST ECB encrypt test vector

Load FIPS 197 Appendix B test key and plaintext, set mode=ECB,
operation=encrypt, trigger start, and verify DATA_OUT matches the known ciphertext.

Priority: high
Coverage Target: cp_mode.ecb cross cp_op.encrypt cross cp_kat
"""
import cocotb
from cocotb.triggers import Timer, RisingEdge
from .helpers import generate_clock, generate_reset

# Test vectors from FIPS 197 Appendix B
FIPS197_KEY = 0x2B7E151628AED2A6ABF7158809CF4F3C
FIPS197_PT = 0x3243F6A8885A308D313198A2E0370734
FIPS197_CT = 0x3925841D02DC09FBDC118597196A0B32


async def write_aes_csr(dut, addr, data):
    """Write a 32-bit CSR register via TL-UL."""
    dut.tl_a_valid_i.value = 1
    dut.tl_a_opcode_i.value = 0  # PutFullData
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
    """Read a 32-bit CSR register via TL-UL."""
    dut.tl_a_valid_i.value = 1
    dut.tl_a_opcode_i.value = 4  # Get
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
    """Write 128-bit value across 4 consecutive 32-bit registers."""
    for i in range(4):
        word = (value >> (32 * (3 - i))) & 0xFFFFFFFF
        addr = start_addr + (i * 4)
        await write_aes_csr(dut, addr, word)
        await Timer(20, unit="ns")


async def read_aes_128(dut, start_addr):
    """Read 128-bit value from 4 consecutive 32-bit registers."""
    result = 0
    for i in range(4):
        addr = start_addr + (i * 4)
        word = await read_aes_csr(dut, addr)
        result = (result << 32) | word
        await Timer(10, unit="ns")
    return result


@cocotb.test()
async def test_vp_aes_001(dut):
    """VP-AES-001: ECB encrypt FIPS 197 test vector"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)

    cocotb.log.info(f"[VP-AES-001] Starting ECB encrypt test")

    # Write key to AES_KEY_0:3 (0x00:0x0C)
    await write_aes_128(dut, 0x00, FIPS197_KEY)
    cocotb.log.info(f"  Key: {FIPS197_KEY:#034x}")

    # Write plaintext to AES_DATA_IN_0:3 (0x20:0x2C)
    await write_aes_128(dut, 0x20, FIPS197_PT)
    cocotb.log.info(f"  PT:  {FIPS197_PT:#034x}")

    # Configure mode=ECB (0), operation=encrypt (0) via AES_CTRL
    await write_aes_csr(dut, 0x40, 0x0)
    await Timer(100, unit="ns")

    # Trigger AES operation via AES_TRIGGER (bit 0 = start)
    await write_aes_csr(dut, 0x44, 0x1)
    await Timer(500, unit="ns")

    # Wait for completion: poll AES_STATUS (0x48) until output_valid (bit 1)
    for _ in range(10000):
        status = await read_aes_csr(dut, 0x48)
        if (status & 0x2) != 0:  # output_valid bit set
            break
        await Timer(10, unit="ns")

    # Read ciphertext from AES_DATA_OUT_0:3 (0x30:0x3C)
    ct = await read_aes_128(dut, 0x30)
    cocotb.log.info(f"  CT:  {ct:#034x}")
    cocotb.log.info(f"  EXP: {FIPS197_CT:#034x}")

    assert (
        ct == FIPS197_CT
    ), f"ECB encrypt mismatch: got {ct:#034x}, expected {FIPS197_CT:#034x}"
    cocotb.log.info(f"[VP-AES-001] ✓ PASS")
