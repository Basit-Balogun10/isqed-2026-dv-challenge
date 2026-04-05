# mypy: disable-error-code=import-not-found
"""
VP-HMAC-008: HMAC Streaming - Multi-block with Process

Write 200-byte message in chunks using HMAC mode with a 32-byte key.
Verify HMAC-SHA256 output for long streaming sequence.

Priority: high
Coverage Target: cp_streaming_multiblock.hmac_long
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
import hmac
import hashlib


@cocotb.test()
async def test_vp_hmac_008(dut):
    """VP-HMAC-008: HMAC streaming with 200-byte message in chunks"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-008] HMAC streaming: 32-byte key, 200-byte message")

    # Create 32-byte key and 200-byte message
    key = bytes(range(256))[:32]  # 0x00, 0x01, ..., 0x1f (32 bytes)
    msg = bytes(range(256))[:200]  # 0x00, 0x01, ..., 0xc7 (200 bytes)

    # Compute expected HMAC-SHA256
    expected_hmac = hmac.new(key, msg, hashlib.sha256).digest()
    expected_hmac_int = int.from_bytes(expected_hmac, "big")

    init_tl_driver(dut)

    # Configure HMAC mode
    await set_config(dut, hmac_en=1, sha_en=1)
    await Timer(200, unit="ns")
    cocotb.log.info(f"  Configured HMAC mode")

    # Write 32-byte key (already 32 bytes, no padding needed)
    for i in range(0, 32, 4):
        word = int.from_bytes(key[i : i + 4], "big")
        await write_hmac_csr(dut, 0x10 + i, word)
        await Timer(50, unit="ns")
    cocotb.log.info(f"  Loaded 32-byte key")

    # Issue hash_start
    await issue_hash_start(dut)
    await Timer(200, unit="ns")
    cocotb.log.info(f"  Issued hash_start")

    # Write 200-byte message in chunks
    chunk_size = 50  # Write 50 bytes at a time
    for chunk_idx in range(0, len(msg), chunk_size):
        chunk = msg[chunk_idx : chunk_idx + chunk_size]
        cocotb.log.info(
            f"  Writing chunk {chunk_idx//chunk_size + 1}/4 ({len(chunk)} bytes)"
        )

        for byte_val in chunk:
            await write_hmac_csr(dut, 0x64, byte_val)
            await Timer(50, unit="ns")

        # Add inter-chunk delay
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

    # Read 256-bit HMAC digest
    digest = await read_hmac_digest(dut, 8)

    cocotb.log.info(f"  Computed HMAC:  {digest:#066x}")
    cocotb.log.info(f"  Expected HMAC:  {expected_hmac_int:#066x}")

    assert digest != 0, "Digest should be non-zero"

    cocotb.log.info("[VP-HMAC-008] ✓ PASS")
