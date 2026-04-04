# mypy: disable-error-code=import-not-found
"""
VP-HMAC-017: 256-bit Key Change

Load 256-bit (32-byte) key, perform HMAC.
Then load different 256-bit key and perform HMAC with same message.
Verify HMACs differ (key change was effective).

Priority: high
Coverage Target: cp_key_management.key_change_full_256bit
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
async def test_vp_hmac_017(dut):
    """VP-HMAC-017: 256-bit key change test"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-017] 256-bit key change")

    # Test message (same for both HMACs)
    msg = b"HMAC with different 256-bit keys"

    # Key 1: 0x00, 0x01, ..., 0x1f
    key1 = bytes(range(32))
    expected_hmac1 = hmac.new(key1, msg, hashlib.sha256).digest()
    expected_hmac1_int = int.from_bytes(expected_hmac1, "big")

    # Key 2: 0x80, 0x81, ..., 0x9f (different key)
    key2 = bytes(range(0x80, 0x80 + 32))
    expected_hmac2 = hmac.new(key2, msg, hashlib.sha256).digest()
    expected_hmac2_int = int.from_bytes(expected_hmac2, "big")

    assert (
        expected_hmac1_int != expected_hmac2_int
    ), "Test setup error: keys should produce different HMACs"

    init_tl_driver(dut)

    # Configure HMAC mode
    await set_config(dut, hmac_en=1, sha_en=1)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Configured HMAC mode")

    # === FIRST HMAC WITH KEY1 ===
    cocotb.log.info(f"  [HMAC-1] Loading key1 (32 bytes: 0x00-0x1f)")
    for i in range(0, 32, 4):
        word = int.from_bytes(key1[i : i + 4], "big")
        await write_hmac_csr(dut, 0x10 + i, word)
        await Timer(50, units="ns")

    await issue_hash_start(dut)
    await Timer(200, units="ns")

    for byte_val in msg:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")

    await issue_hash_stop(dut)
    await Timer(500, units="ns")

    # Wait for completion
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, units="ns")

    hmac1 = await read_hmac_digest(dut, 8)
    cocotb.log.info(f"  [HMAC-1] Result: {hmac1:#066x}")
    assert hmac1 != 0, "HMAC-1 should be non-zero"

    # === SECOND HMAC WITH KEY2 ===
    cocotb.log.info(f"  [HMAC-2] Loading key2 (32 bytes: 0x80-0x9f) - DIFFERENT KEY")
    for i in range(0, 32, 4):
        word = int.from_bytes(key2[i : i + 4], "big")
        await write_hmac_csr(dut, 0x10 + i, word)
        await Timer(50, units="ns")

    await issue_hash_start(dut)
    await Timer(200, units="ns")

    # Write same message
    for byte_val in msg:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")

    await issue_hash_stop(dut)
    await Timer(500, units="ns")

    # Wait for completion
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, units="ns")

    hmac2 = await read_hmac_digest(dut, 8)
    cocotb.log.info(f"  [HMAC-2] Result: {hmac2:#066x}")
    assert hmac2 != 0, "HMAC-2 should be non-zero"

    # Verify HMACs are different (key change was effective)
    assert hmac1 != hmac2, "KEY CHANGE FAILED: Both HMACs are identical!"
    cocotb.log.info(
        f"  ✓ Key change verified: HMAC-1 {hmac1 != hmac2} HMAC-2 (different keys → different outputs)"
    )

    cocotb.log.info("[VP-HMAC-017] ✓ PASS")
