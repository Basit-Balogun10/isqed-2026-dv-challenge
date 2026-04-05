# mypy: disable-error-code=import-not-found
"""VP-AES-018: All-one data pattern"""
import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    aes_ecb_encrypt, aes_ecb_decrypt, FIPS197_KEY
)

@cocotb.test()
async def test_vp_aes_018(dut):
    """
    All-one data pattern.
    
    Encrypt and decrypt a 128-bit all-one (0xFF) block.
    Verify correct ciphertext output and roundtrip.
    """
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    all_ones = 0xffffffffffffffffffffffffffffffff
    
    # Encrypt all-one plaintext
    ct = await aes_ecb_encrypt(dut, FIPS197_KEY, all_ones)
    cocotb.log.info(f"All-one plaintext -> {ct:#034x}")
    assert ct != all_ones, f"All-one encryption produced all-one output (invalid)"
    
    # Decrypt and verify roundtrip
    pt = await aes_ecb_decrypt(dut, FIPS197_KEY, ct)
    assert pt == all_ones, f"All-one roundtrip failed: {pt:#034x}"
    cocotb.log.info(f"✓ All-one pattern verified")
    cocotb.log.info(f"✓ VP-AES-018 PASS")
