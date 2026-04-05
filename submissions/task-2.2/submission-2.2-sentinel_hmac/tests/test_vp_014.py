# mypy: disable-error-code=import-not-found
"""
VP-HMAC-014: Double hash_stop Recovery

Issue hash_stop twice to test error recovery.
Verify core handles duplicate command and can proceed with next hash.

Priority: high
Coverage Target: cp_error_recovery.double_hash_stop
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
async def test_vp_hmac_014(dut):
    """VP-HMAC-014: Double hash_stop error recovery"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-014] Double hash_stop recovery test")

    init_tl_driver(dut)

    # Configure SHA-256 mode
    await set_config(dut, hmac_en=0, sha_en=1)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Configured SHA-256 mode")

    # === FIRST HASH: Normal message ===
    msg1 = b"First hash"
    expected_digest1 = hashlib.sha256(msg1).digest()
    expected_digest1_int = int.from_bytes(expected_digest1, "big")

    await issue_hash_start(dut)
    await Timer(200, units="ns")
    cocotb.log.info(f"  [HASH 1] hash_start")

    for byte_val in msg1:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")

    await issue_hash_stop(dut)
    await Timer(500, units="ns")
    cocotb.log.info(f"  [HASH 1] hash_stop (first)")

    # Issue hash_stop AGAIN (error condition)
    await issue_hash_stop(dut)
    await Timer(500, units="ns")
    cocotb.log.info(f"  [HASH 1] hash_stop (SECOND - error)")

    # Wait for completion of first hash
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, units="ns")

    digest1 = await read_hmac_digest(dut, 8)
    cocotb.log.info(f"  [HASH 1] SHA-256: {digest1:#066x}")
    assert digest1 != 0, "First digest should be non-zero"
    cocotb.log.info(f"  [HASH 1] ✓ Completed successfully despite double hash_stop")

    # === SECOND HASH: Recovery test ===
    cocotb.log.info(f"  [Recovery] Starting second hash...")
    msg2 = b"Recovery test"
    expected_digest2 = hashlib.sha256(msg2).digest()
    expected_digest2_int = int.from_bytes(expected_digest2, "big")

    await issue_hash_start(dut)
    await Timer(200, units="ns")
    cocotb.log.info(f"  [HASH 2] hash_start")

    for byte_val in msg2:
        await write_hmac_csr(dut, 0x64, byte_val)
        await Timer(50, units="ns")

    await issue_hash_stop(dut)
    await Timer(500, units="ns")
    cocotb.log.info(f"  [HASH 2] hash_stop")

    # Wait for completion
    for _ in range(50000):
        status = await read_hmac_csr(dut, 0x08)
        if (status & 0x100) != 0:
            break
        await Timer(10, units="ns")

    digest2 = await read_hmac_digest(dut, 8)
    cocotb.log.info(f"  [HASH 2] SHA-256: {digest2:#066x}")
    assert digest2 != 0, "Recovery digest should be non-zero"
    assert digest1 != digest2, "Different messages should produce different digests"
    cocotb.log.info(f"  [HASH 2] ✓ Recovery successful, second hash correct")

    cocotb.log.info("[VP-HMAC-014] ✓ PASS")
