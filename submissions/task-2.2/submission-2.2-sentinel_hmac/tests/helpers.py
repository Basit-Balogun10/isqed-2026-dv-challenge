"""
Pytest configuration and shared fixtures for HMAC tests.

Provides:
- Helper functions for TL-UL CSR access (via reusable TlUlDriver)
- Test vectors (RFC 4231, empty message, etc.)
- Common HMAC/SHA-256 operations
"""

import sys

sys.path.insert(0, ".")

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge
from testbench.tl_ul_agent import TlUlDriver
from testbench.functional_coverage import (
    sample_config,
    sample_interrupt_write,
    sample_message_length,
)

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
# TEST VECTORS - RFC 4231 HMAC-SHA256 Test Cases
# ============================================================================

# RFC 4231 Test Case 1: simple key and message
RFC4231_TC1_KEY = b"\x0b" * 20
RFC4231_TC1_MSG = b"Hi There"
RFC4231_TC1_EXPECTED = bytes.fromhex(
    "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726ecbdf2d6fab7bb"
)

# RFC 4231 Test Case 2: key = "Jefe", message
RFC4231_TC2_KEY = b"Jefe"
RFC4231_TC2_MSG = b"what do ya want for nothing?"
RFC4231_TC2_EXPECTED = bytes.fromhex(
    "5bdccb7b6264581d1ed04c3e47c6e47a71f07c8e0c0211a1c7d6a2b5fafeb71c"
)

# SHA-256 of empty string
SHA256_EMPTY = bytes.fromhex(
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)

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


async def write_hmac_csr(dut, addr, data):
    """Write a 32-bit CSR register via TL-UL using TlUlDriver."""
    if _tl_driver is None:
        init_tl_driver(dut)
    await _tl_driver.write_reg(addr, data, mask=0xF, source=0)

    if addr == 0x5C:
        sample_interrupt_write("enable")
    elif addr == 0x60:
        sample_interrupt_write("test")


async def read_hmac_csr(dut, addr):
    """Read a 32-bit CSR register via TL-UL using TlUlDriver."""
    if _tl_driver is None:
        init_tl_driver(dut)
    return await _tl_driver.read_reg(addr, source=0)


async def write_hmac_msg_fifo(dut, byte_data):
    """Write message data to HMAC MSG_FIFO (address 0x64)."""
    sample_message_length(len(byte_data))
    for byte_val in byte_data:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, unit="ns")


async def read_hmac_digest(dut, num_words=8):
    """Read 256-bit digest from DIGEST registers (0x30-0x4C)."""
    digest = 0
    for i in range(num_words):
        word = await read_hmac_csr(dut, 0x30 + (i * 4))
        digest = (digest << 32) | word
    return digest


async def check_sha_status(dut):
    """Check SHA status from STATUS register (0x08)."""
    status = await read_hmac_csr(dut, 0x08)
    return status


async def set_config(dut, hmac_en, sha_en, endian_swap=0, digest_swap=0):
    """Configure HMAC/SHA mode via CFG register (0x00)."""
    sample_config(hmac_en, sha_en)
    cfg = (
        (hmac_en & 1)
        | ((sha_en & 1) << 1)
        | ((endian_swap & 1) << 2)
        | ((digest_swap & 1) << 3)
    )
    await write_hmac_csr(dut, 0x00, cfg)
    await Timer(100, unit="ns")


async def issue_hash_start(dut):
    """Issue hash_start command via CMD register (0x04)."""
    await write_hmac_csr(dut, 0x04, 0x1)
    await Timer(200, unit="ns")


async def issue_hash_process(dut):
    """Issue hash_process command."""
    await write_hmac_csr(dut, 0x04, 0x2)
    await Timer(200, unit="ns")


async def issue_hash_stop(dut):
    """Issue hash_stop command."""
    await write_hmac_csr(dut, 0x04, 0x4)
    await Timer(200, unit="ns")


async def wait_for_digest_valid(dut, max_us=1000):
    """Wait for digest_valid bit in STATUS."""
    for _ in range(max_us * 100):
        status = await check_sha_status(dut)
        if (status & 0x100) != 0:  # digest_valid bit
            return True
        await Timer(10, unit="ns")
    return False


async def hmac_sha256_hash(dut, message):
    """Perform SHA-256 hash on message and return digest."""
    await set_config(dut, hmac_en=0, sha_en=1)
    await issue_hash_start(dut)
    await write_hmac_msg_fifo(dut, message)
    await issue_hash_stop(dut)
    await wait_for_digest_valid(dut)
    return await read_hmac_digest(dut)
