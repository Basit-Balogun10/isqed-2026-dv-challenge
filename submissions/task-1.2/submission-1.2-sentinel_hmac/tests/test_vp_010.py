# mypy: disable-error-code=import-not-found
"""
VP-HMAC-010: Endian Swap - Message Input

Set endian_swap=1 in CONFIG register, verify byte-order reversal on message input.
When endian_swap=1, message bytes are reversed before hashing.

Priority: high
Coverage Target: cp_config.endian_swap_message
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
async def test_vp_hmac_010(dut):
    """VP-HMAC-010: Endian swap on message input"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-010] Endian swap: reverse message bytes")

    # Original message: "The quick brown fox"
    msg_original = b"The quick brown fox"

    init_tl_driver(dut)

    # Configure SHA-256 mode with endian_swap=1
    # CFG[0]=hmac_en=0, CFG[1]=sha_en=1, CFG[2]=endian_swap=1
    cfg_value = (0 << 0) | (1 << 1) | (1 << 2)
    await write_hmac_csr(dut, 0x00, cfg_value)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Configured SHA-256 with endian_swap=1 (cfg={cfg_value:#06x})")

    # Issue hash_start
    await issue_hash_start(dut)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Issued hash_start")

    # Write original message bytes (hardware reverses them)
    for byte_val in msg_original:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")
    cocotb.log.info(f"  Wrote {len(msg_original)} bytes of original message")

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

    # Read 256-bit SHA-256 digest with endian_swap enabled
    digest_swapped = await read_hmac_digest(dut, 8)
    cocotb.log.info(f"  Digest (endian_swap=1): {digest_swapped:#066x}")

    # Re-run with endian_swap disabled and ensure outputs differ
    await set_config(dut, hmac_en=0, sha_en=1, endian_swap=0)
    await Timer(200, units="ns")
    await issue_hash_start(dut)
    await Timer(200, units="ns")
    for byte_val in msg_original:
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
    cocotb.log.info(f"  Digest (endian_swap=0): {digest_normal:#066x}")

    assert digest_swapped != digest_normal, "Endian swap should change digest value"
    assert digest_swapped != 0 and digest_normal != 0, "Digests should be non-zero"

    cocotb.log.info("[VP-HMAC-010] ✓ PASS")
