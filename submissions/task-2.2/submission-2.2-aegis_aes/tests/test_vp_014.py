# mypy: disable-error-code=import-not-found
"""VP-AES-014: Mode switching ECB to CBC"""
import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    aes_ecb_encrypt, aes_cbc_encrypt,
    FIPS197_KEY, FIPS197_PT, FIPS197_CT,
    NIST_CBC_KEY, NIST_CBC_IV, NIST_CBC_PT1, NIST_CBC_CT1
)

@cocotb.test()
async def test_vp_aes_014(dut):
    """
    Mode switching ECB to CBC.
    
    Perform an ECB encrypt, then change AES_CTRL to CBC mode 
    and perform another operation with an IV. Verify the mode switch works.
    """
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    # ECB encrypt
    ecb_result = await aes_ecb_encrypt(dut, FIPS197_KEY, FIPS197_PT)
    assert ecb_result == FIPS197_CT, f"ECB mode failed: {ecb_result:#034x}"
    cocotb.log.info(f"✓ ECB encrypt worked")
    
    # Switch to CBC and encrypt
    cbc_result = await aes_cbc_encrypt(dut, NIST_CBC_KEY, NIST_CBC_IV, NIST_CBC_PT1)
    assert cbc_result == NIST_CBC_CT1, f"CBC after mode switch failed: {cbc_result:#034x}"
    cocotb.log.info(f"✓ Mode switch to CBC successful")
    cocotb.log.info(f"✓ VP-AES-014 PASS")
