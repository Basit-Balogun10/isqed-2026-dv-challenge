"""
Pytest configuration and shared fixtures for AES tests.

Provides:
- Helper functions for TL-UL CSR access (via reusable TlUlDriver)
- Test vectors (FIPS 197, NIST SP 800-38A)
- Common AES operations (encrypt/decrypt ECB/CBC)
"""

import sys

sys.path.insert(0, ".")

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge
from testbench.tl_ul_agent import TlUlDriver

# ============================================================================
# CLOCK & RESET GENERATION
# ============================================================================


async def generate_clock(dut, period_ns=10):
    """Start clock generation for the testbench"""
    clock = Clock(dut.clk_i, period_ns, unit="ns")
    cocotb.start_soon(clock.start())
    await Timer(50, unit="ns")


async def generate_reset(dut, cycles=5):
    """Generate active-low reset pulse"""
    dut.rst_ni.value = 0
    for _ in range(cycles):
        await RisingEdge(dut.clk_i)
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)


# ============================================================================
# TEST VECTORS
# ============================================================================

FIPS197_KEY = 0x2B7E151628AED2A6ABF7158809CF4F3C
FIPS197_PT = 0x3243F6A8885A308D313198A2E0370734
FIPS197_CT = 0x3925841D02DC09FBDC118597196A0B32

NIST_CBC_KEY = 0x2B7E151628AED2A6ABF7158809CF4F3C
NIST_CBC_IV = 0x000102030405060708090A0B0C0D0E0F
NIST_CBC_PT1 = 0x6BC1BEE22E409F96E93D7E117393172A
NIST_CBC_CT1 = 0x7649ABAC8119B246CEE98E9B12E9197D
NIST_CBC_PT2 = 0xAE2D8A571E03AC9C9EB76FAC45AF8E51
NIST_CBC_CT2 = 0x5086CB9B507219EE95DB113A917678B2

ZERO_KEY = 0x00000000000000000000000000000000
ONES_KEY = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF


# ============================================================================
# TL-UL DRIVER INSTANCE (initialized in test setup)
# ============================================================================

_tl_driver = None


def init_tl_driver(dut):
    """Initialize the TL-UL driver for CSR access."""
    global _tl_driver
    _tl_driver = TlUlDriver(dut, clk_signal="clk_i")


# ============================================================================
# CSR HELPERS (delegated to TlUlDriver)
# ============================================================================


async def write_aes_csr(dut, addr, data):
    """Write a 32-bit CSR register via TL-UL using TlUlDriver."""
    if _tl_driver is None:
        init_tl_driver(dut)
    await _tl_driver.write_reg(addr, data, mask=0xF, source=0)


async def read_aes_csr(dut, addr):
    """Read a 32-bit CSR register via TL-UL using TlUlDriver."""
    if _tl_driver is None:
        init_tl_driver(dut)
    return await _tl_driver.read_reg(addr, source=0)


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


async def aes_trigger_start(dut):
    """Issue AES start operation trigger."""
    await write_aes_csr(dut, 0x44, 0x1)
    await Timer(500, unit="ns")


async def aes_wait_done(dut, max_us=100):
    """Wait for AES operation to complete (output_valid)."""
    for _ in range(max_us * 100):
        status = await read_aes_csr(dut, 0x48)
        if (status & 0x2) != 0:
            return True
        await Timer(10, unit="ns")
    return False


async def aes_ecb_encrypt(dut, key, plaintext):
    """Perform ECB encryption and return ciphertext."""
    await write_aes_128(dut, 0x00, key)
    await write_aes_128(dut, 0x20, plaintext)
    await write_aes_csr(dut, 0x40, 0x0)
    await aes_trigger_start(dut)
    await aes_wait_done(dut)
    return await read_aes_128(dut, 0x30)


async def aes_ecb_decrypt(dut, key, ciphertext):
    """Perform ECB decryption and return plaintext."""
    await write_aes_128(dut, 0x00, key)
    await write_aes_128(dut, 0x20, ciphertext)
    await write_aes_csr(dut, 0x40, 0x2)
    await aes_trigger_start(dut)
    await aes_wait_done(dut)
    return await read_aes_128(dut, 0x30)


async def aes_cbc_encrypt(dut, key, iv, plaintext):
    """Perform CBC encryption and return ciphertext."""
    await write_aes_128(dut, 0x00, key)
    await write_aes_128(dut, 0x10, iv)
    await write_aes_128(dut, 0x20, plaintext)
    await write_aes_csr(dut, 0x40, 0x1)
    await aes_trigger_start(dut)
    await aes_wait_done(dut)
    return await read_aes_128(dut, 0x30)


async def aes_cbc_decrypt(dut, key, iv, ciphertext):
    """Perform CBC decryption and return plaintext."""
    await write_aes_128(dut, 0x00, key)
    await write_aes_128(dut, 0x10, iv)
    await write_aes_128(dut, 0x20, ciphertext)
    await write_aes_csr(dut, 0x40, 0x3)
    await aes_trigger_start(dut)
    await aes_wait_done(dut)
    return await read_aes_128(dut, 0x30)
