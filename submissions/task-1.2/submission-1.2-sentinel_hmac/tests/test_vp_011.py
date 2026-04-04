# mypy: disable-error-code=import-not-found
"""
VP-HMAC-011: Digest Swap - Output

Set digest_swap=1 in CONFIG register, verify 32-bit word order reversal in output digest.
When digest_swap=1, the 8 x 32-bit words of the digest are reversed.

Priority: high
Coverage Target: cp_config.digest_swap_output
"""
import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    write_hmac_csr,
    read_hmac_csr,
    set_config,
    issue_hash_start,
    issue_hash_stop,
    read_hmac_digest,
)
import hashlib


@cocotb.test()
async def test_vp_hmac_011(dut):
    """VP-HMAC-011: Digest swap on output"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-011] Digest swap: reverse 256-bit output word order")

    # Test message
    msg = b"Digest swap test"

    init_tl_driver(dut)

    # First run with digest_swap disabled to get baseline digest words
    await set_config(dut, hmac_en=0, sha_en=1, digest_swap=0)
    await Timer(200, units="ns")
    cocotb.log.info("  Configured SHA-256 with digest_swap=0")

    await issue_hash_start(dut)
    await Timer(200, units="ns")
    for byte_val in msg:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")
    await issue_hash_stop(dut)
    await Timer(500, units="ns")
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, units="ns")
    digest_normal = await read_hmac_digest(dut, 8)

    # Second run with digest_swap enabled
    cfg_value = (0 << 0) | (1 << 1) | (1 << 3)
    await write_hmac_csr(dut, 0x00, cfg_value)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Configured SHA-256 with digest_swap=1 (cfg={cfg_value:#06x})")

    # Issue hash_start
    await issue_hash_start(dut)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Issued hash_start")

    # Write message
    for byte_val in msg:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")
    cocotb.log.info(f"  Wrote {len(msg)} bytes")

    # Issue hash_stop
    await issue_hash_stop(dut)
    await Timer(500, units="ns")
    cocotb.log.info(f"  Issued hash_stop")

    # Wait for completion
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, units="ns")

    # Read 256-bit digest (with per-word byte swap applied by hardware)
    digest_swapped = await read_hmac_digest(dut, 8)

    # RTL applies endian_swap32 to each 32-bit digest word when digest_swap=1.
    expected_swapped = 0
    for i in range(8):
        w = (digest_normal >> (32 * (7 - i))) & 0xFFFFFFFF
        w_swapped = (
            ((w & 0xFF) << 24)
            | ((w & 0xFF00) << 8)
            | ((w >> 8) & 0xFF00)
            | ((w >> 24) & 0xFF)
        )
        expected_swapped = (expected_swapped << 32) | w_swapped

    cocotb.log.info(f"  Digest normal:     {digest_normal:#066x}")
    cocotb.log.info(f"  Digest swap=1:     {digest_swapped:#066x}")
    cocotb.log.info(f"  Expected swapped:  {expected_swapped:#066x}")

    assert (
        digest_swapped == expected_swapped
    ), f"Digest swap mismatch: got {digest_swapped:#066x}, expected {expected_swapped:#066x}"

    cocotb.log.info("[VP-HMAC-011] ✓ PASS")
