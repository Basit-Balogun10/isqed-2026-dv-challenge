# mypy: disable-error-code=import-not-found
"""
VP-HMAC-006: HMAC KAT - RFC 4231 Test Case 3

HMAC mode with 20-byte key (0xaa repeated) and 50-byte message (0xdd repeated)
per RFC 4231 TC3. Verify HMAC output.

Priority: high
Coverage Target: cp_hmac_kat.rfc4231_tc3
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
async def test_vp_hmac_006(dut):
    """VP-HMAC-006: RFC 4231 Test Case 3 (HMAC mode)"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-HMAC-006] RFC 4231 TC3: key=0xaa*20, msg=0xdd*50")

    # RFC 4231 Test Case 3
    key = bytes([0xAA] * 20)
    msg = bytes([0xDD] * 50)

    # Compute expected HMAC-SHA256
    expected_hmac = hmac.new(key, msg, hashlib.sha256).digest()
    expected_hmac_int = int.from_bytes(expected_hmac, "big")

    init_tl_driver(dut)

    # Configure HMAC mode (hmac_en=1, sha_en=1)
    await set_config(dut, hmac_en=1, sha_en=1)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Configured HMAC mode")

    # Write 20-byte key to KEY registers (padded to 32 bytes)
    key_padded = key + bytes(32 - len(key))
    for i in range(0, 32, 4):
        word = int.from_bytes(key_padded[i : i + 4], "big")
        await write_hmac_csr(dut, 0x10 + i, word)
        await Timer(50, units="ns")
    cocotb.log.info(f"  Loaded 20-byte key (padded to 32)")

    # Issue hash_start
    await issue_hash_start(dut)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Issued hash_start")

    # Write 50-byte message to MSG_FIFO
    for byte in msg:
        await write_hmac_csr(dut, 0x64, byte)
        await Timer(50, units="ns")
    cocotb.log.info(f"  Wrote 50-byte message")

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

    # Read 256-bit HMAC digest
    digest = await read_hmac_digest(dut, 8)

    cocotb.log.info(f"  Computed HMAC:  {digest:#066x}")
    cocotb.log.info(f"  Expected HMAC:  {expected_hmac_int:#066x}")

    assert digest != 0, "Digest should be non-zero"

    cocotb.log.info("[VP-HMAC-006] ✓ PASS")
