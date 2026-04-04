# mypy: disable-error-code=import-not-found
"""VP-AES-013: CBC encrypt-then-decrypt roundtrip"""

import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    aes_cbc_encrypt,
    aes_cbc_decrypt,
    NIST_CBC_KEY,
    NIST_CBC_IV,
    NIST_CBC_PT1,
)


@cocotb.test()
async def test_vp_aes_013(dut):
    """
    CBC encrypt-then-decrypt roundtrip.

    Encrypt a block in CBC mode, note the ciphertext and updated IV.
    Decrypt using the original IV and key, and verify plaintext recovery.
    """
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    # Encrypt
    ct = await aes_cbc_encrypt(dut, NIST_CBC_KEY, NIST_CBC_IV, NIST_CBC_PT1)
    cocotb.log.info(f"Encrypted: {ct:#034x}")

    # Decrypt using original IV
    pt = await aes_cbc_decrypt(dut, NIST_CBC_KEY, NIST_CBC_IV, ct)
    cocotb.log.info(f"Decrypted: {pt:#034x}, Original: {NIST_CBC_PT1:#034x}")

    assert (
        pt == NIST_CBC_PT1
    ), f"CBC roundtrip failed: {pt:#034x} vs {NIST_CBC_PT1:#034x}"
    cocotb.log.info(f"✓ VP-AES-013 PASS")
