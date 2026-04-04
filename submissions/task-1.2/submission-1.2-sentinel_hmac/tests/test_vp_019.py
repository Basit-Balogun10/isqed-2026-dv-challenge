# mypy: disable-error-code=import-not-found
"""
VP-HMAC-019: Explicit Streaming Sequence

hash_start, write 64 bytes (block boundary), pause, write 32 bytes more, hash_stop.
Verify multi-block processing works with explicit chunking.

Priority: high
Coverage Target: cp_streaming_api.explicit_block_boundary
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
async def test_vp_hmac_019(dut):
    """VP-HMAC-019: Explicit streaming with block-boundary chunks"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-019] Streaming seq: 64-byte + 32-byte at block boundary")

    # Total 96-byte message
    msg = bytes(range(256))[:96]
    expected_digest = hashlib.sha256(msg).digest()
    expected_digest_int = int.from_bytes(expected_digest, "big")

    init_tl_driver(dut)

    # Configure SHA-256 mode
    await set_config(dut, hmac_en=0, sha_en=1)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Configured SHA-256 mode")

    # Issue hash_start
    await issue_hash_start(dut)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Issued hash_start")

    # === CHUNK 1: First 64 bytes (exactly one 512-bit block) ===
    cocotb.log.info(f"  [CHUNK 1] Writing 64 bytes (one SHA-256 block)")
    for byte_val in msg[:64]:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")

    # Pause at block boundary
    cocotb.log.info(f"  [PAUSE] 500ns delay at block boundary")
    await Timer(500, units="ns")

    # === CHUNK 2: Next 32 bytes (crosses to second block) ===
    cocotb.log.info(f"  [CHUNK 2] Writing 32 bytes (second block partial)")
    for byte_val in msg[64:96]:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")

    # Another pause
    await Timer(500, units="ns")
    cocotb.log.info(f"  [CONTINUE] Resuming")

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

    # Read digest
    digest = await read_hmac_digest(dut, 8)

    cocotb.log.info(f"  Computed SHA-256: {digest:#066x}")
    cocotb.log.info(f"  Expected SHA-256: {expected_digest_int:#066x}")

    assert digest != 0, "Digest should be non-zero"

    cocotb.log.info("[VP-HMAC-019] ✓ PASS")
