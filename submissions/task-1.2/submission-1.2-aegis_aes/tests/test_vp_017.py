# mypy: disable-error-code=import-not-found
"""VP-AES-017: All-zero data pattern"""
import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    aes_ecb_encrypt, aes_ecb_decrypt, FIPS197_KEY
)

@cocotb.test()
async def test_vp_aes_017(dut):
    """
    All-zero data pattern.
    
    Encrypt and decrypt a 128-bit all-zero block with a known key.
    Verify ciphertext is non-zero and roundtrip succeeds.
    """
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    all_zero = 0x00000000000000000000000000000000
    
    # Encrypt all-zero plaintext
    ct = await aes_ecb_encrypt(dut, FIPS197_KEY, all_zero)
    cocotb.log.info(f"All-zero plaintext -> {ct:#034x}")
    assert ct != 0, f"All-zero encryption produced zero output (invalid)"
    
    # Decrypt and verify roundtrip
    pt = await aes_ecb_decrypt(dut, FIPS197_KEY, ct)
    assert pt == all_zero, f"All-zero roundtrip failed: {pt:#034x}"
    cocotb.log.info(f"✓ All-zero pattern verified")
    cocotb.log.info(f"✓ VP-AES-017 PASS")
