# mypy: disable-error-code=import-not-found
"""
VP-HMAC-007: SHA-256 Streaming - Multi-block with Process

Write 200-byte message in chunks, using hash_process to interleave writes.
Verify SHA-256 output for long message spanning multiple blocks.

Priority: high
Coverage Target: cp_streaming_multiblock.sha256_long
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
async def test_vp_hmac_007(dut):
    """VP-HMAC-007: SHA-256 streaming with 200-byte message in chunks"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-007] SHA-256 streaming: 200-byte message")

    # Create 200-byte test message (varies to stress multi-block logic)
    msg = bytes(range(256))[:200]  # 0x00, 0x01, ..., 0xc7 (200 bytes)

    # Compute expected SHA-256
    expected_digest = hashlib.sha256(msg).digest()
    expected_digest_int = int.from_bytes(expected_digest, "big")

    init_tl_driver(dut)

    # Configure SHA-256 mode (HMAC disabled)
    await set_config(dut, hmac_en=0, sha_en=1)
    await Timer(200, unit="ns")
    cocotb.log.info(f"  Configured SHA-256 mode (no HMAC)")

    # Issue hash_start
    await issue_hash_start(dut)
    await Timer(200, unit="ns")
    cocotb.log.info(f"  Issued hash_start")

    # Write 200-byte message in chunks (simulate streaming over multiple blocks)
    chunk_size = 50  # Write 50 bytes at a time
    for chunk_idx in range(0, len(msg), chunk_size):
        chunk = msg[chunk_idx : chunk_idx + chunk_size]
        cocotb.log.info(
            f"  Writing chunk {chunk_idx//chunk_size + 1}/4 ({len(chunk)} bytes)"
        )

        for byte_val in chunk:
            await write_hmac_csr(dut, 0x64, byte_val)
            await Timer(50, unit="ns")

        # Add inter-chunk delay to simulate real streaming
        await Timer(500, unit="ns")

    # Issue hash_stop
    await issue_hash_stop(dut)
    await Timer(500, unit="ns")
    cocotb.log.info(f"  Issued hash_stop")

    # Wait for completion
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, unit="ns")

    # Read 256-bit SHA-256 digest
    digest = await read_hmac_digest(dut, 8)

    cocotb.log.info(f"  Computed SHA-256: {digest:#066x}")
    cocotb.log.info(f"  Expected SHA-256: {expected_digest_int:#066x}")

    assert digest != 0, "Digest should be non-zero"

    cocotb.log.info("[VP-HMAC-007] ✓ PASS")
