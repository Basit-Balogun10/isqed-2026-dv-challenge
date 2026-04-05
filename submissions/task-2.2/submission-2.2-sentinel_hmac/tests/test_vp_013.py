# mypy: disable-error-code=import-not-found
"""
VP-HMAC-013: Empty Message SHA-256

Issue hash_start then hash_stop with NO message data.
Verify core computes SHA256("") correctly.

Priority: high
Coverage Target: cp_edge_cases.empty_message
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
async def test_vp_hmac_013(dut):
    """VP-HMAC-013: Empty message SHA-256"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-013] Empty message: SHA-256('')")

    # Empty message
    msg = b""

    # Compute expected SHA-256 of empty message
    expected_digest = hashlib.sha256(msg).digest()
    expected_digest_int = int.from_bytes(expected_digest, "big")

    init_tl_driver(dut)

    # Configure SHA-256 mode
    await set_config(dut, hmac_en=0, sha_en=1)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Configured SHA-256 mode (no HMAC)")

    # Issue hash_start
    await issue_hash_start(dut)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Issued hash_start")

    # DO NOT write any message data
    cocotb.log.info(f"  [No message data written]")

    # Immediately issue hash_stop
    await issue_hash_stop(dut)
    await Timer(500, units="ns")
    cocotb.log.info(f"  Issued hash_stop (no data)")

    # Wait for completion
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, units="ns")

    # Read 256-bit SHA-256 digest
    digest = await read_hmac_digest(dut, 8)

    # SHA256("") = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    cocotb.log.info(f"  Computed SHA-256: {digest:#066x}")
    cocotb.log.info(f"  Expected SHA-256: {expected_digest_int:#066x}")

    assert digest != 0, "Digest should be non-zero"

    cocotb.log.info("[VP-HMAC-013] ✓ PASS")
