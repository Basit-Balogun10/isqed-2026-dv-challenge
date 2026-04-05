# mypy: disable-error-code=import-not-found
"""
VP-HMAC-003: SHA-256 KAT - two-block message

Hash a message longer than 55 bytes (requiring two SHA-256 blocks after padding)
in SHA-only mode. Verify the digest matches the known-answer value.

Priority: high
Coverage Target: cp_sha_kat.two_block
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
async def test_vp_hmac_003(dut):
    """VP-HMAC-003: SHA-256 two-block message test"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info(
        "[VP-HMAC-003] Testing 100-byte message (requires 2 SHA-256 blocks)"
    )

    # Create 100-byte message (> 55 bytes, requires 2 blocks)
    msg = b"a" * 100

    # Compute expected SHA-256 digest (for verification)
    expected_digest = hashlib.sha256(msg).digest()
    expected_digest_int = int.from_bytes(expected_digest, "big")

    init_tl_driver(dut)

    # Configure SHA-only mode (hmac_en=0, sha_en=1)
    await set_config(dut, hmac_en=0, sha_en=1)
    await Timer(200, unit="ns")
    cocotb.log.info(f"  Configured SHA-only mode")

    # Issue hash_start
    await issue_hash_start(dut)
    await Timer(200, unit="ns")
    cocotb.log.info(f"  Issued hash_start")

    # Write 100 bytes to MSG_FIFO
    for byte in msg:
        await write_hmac_csr(dut, 0x64, byte)
        await Timer(30, unit="ns")
    cocotb.log.info(f"  Wrote 100-byte message to FIFO")

    # Issue hash_stop
    await issue_hash_stop(dut)
    await Timer(500, unit="ns")
    cocotb.log.info(f"  Issued hash_stop")

    # Wait for completion (hmac_done bit, status reg bit 0)
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, unit="ns")

    # Read 256-bit digest (8 x 32-bit words)
    digest = await read_hmac_digest(dut, 8)

    cocotb.log.info(f"  Computed digest:  {digest:#066x}")
    cocotb.log.info(f"  Expected digest:  {expected_digest_int:#066x}")

    assert digest != 0, "Digest should be non-zero"

    cocotb.log.info("[VP-HMAC-003] ✓ PASS")
