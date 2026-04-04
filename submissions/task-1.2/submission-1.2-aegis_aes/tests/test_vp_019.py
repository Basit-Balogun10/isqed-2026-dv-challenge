# mypy: disable-error-code=import-not-found
"""VP-AES-019: Walking-one data pattern"""
import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    aes_ecb_encrypt, FIPS197_KEY
)

@cocotb.test()
async def test_vp_aes_019(dut):
    """
    Walking-one data pattern.
    
    Test with single bits set at different positions.
    Verify each produces a distinct ciphertext.
    """
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    results = {}
    
    # Test walking-one pattern at 8 positions
    for bit_pos in range(8):
        pt = 1 << (16 + bit_pos)  # Various positions
        ct = await aes_ecb_encrypt(dut, FIPS197_KEY, pt)
        results[bit_pos] = ct
        cocotb.log.info(f"Position {bit_pos}: plaintext={pt:#034x} -> {ct:#034x}")
    
    # Verify all ciphertexts are unique
    unique_cts = set(results.values())
    assert len(unique_cts) == 8, f"Not all ciphertexts unique: {len(unique_cts)}/8"
    cocotb.log.info(f"✓ All 8 walking-one results unique")
    cocotb.log.info(f"✓ VP-AES-019 PASS")
