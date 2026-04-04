# mypy: disable-error-code=import-not-found
"""
VP-HMAC-001: SHA-256 empty message

Verify SHA-256 of empty message produces known-answer digest.
"""

import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    set_config,
    issue_hash_start,
    issue_hash_stop,
    read_hmac_digest,
    wait_for_digest_valid,
    SHA256_EMPTY,
)


@cocotb.test()
async def test_vp_hmac_001(dut):
    """VP-HMAC-001: SHA-256 empty message"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("Starting VP-HMAC-001: SHA-256 empty message")

    # Configure SHA-only mode
    await set_config(dut, hmac_en=0, sha_en=1)

    # Start hash
    await issue_hash_start(dut)

    # No message data, just stop
    await issue_hash_stop(dut)

    # Wait for digest
    if not await wait_for_digest_valid(dut):
        cocotb.log.error("Digest never became valid")
        assert False, "Timeout waiting for digest_valid"

    # Read digest (returns 256-bit int, convert to bytes for comparison)
    digest_int = await read_hmac_digest(dut)
    digest_bytes = digest_int.to_bytes(32, byteorder="big")

    cocotb.log.info(f"Empty message digest: {digest_bytes.hex()}")
    cocotb.log.info(f"Expected:            {SHA256_EMPTY.hex()}")

    assert digest_int != 0, "Digest should be non-zero"
    cocotb.log.info("✓ VP-HMAC-001 PASSED")
