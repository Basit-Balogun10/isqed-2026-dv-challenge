# mypy: disable-error-code=import-not-found
"""VP-AES-015: Trigger while busy"""
import cocotb
from cocotb.triggers import Timer, RisingEdge
from .helpers import (
    generate_clock,
    generate_reset,
    write_aes_128, write_aes_csr, aes_trigger_start, aes_wait_done, read_aes_128,
    FIPS197_KEY, FIPS197_PT, FIPS197_CT
)

@cocotb.test()
async def test_vp_aes_015(dut):
    """
    Trigger while busy.
    
    Start an AES operation, then immediately write start=1 to AES_TRIGGER 
    while the engine is busy. Verify the second trigger is ignored 
    and the first operation completes correctly.
    """
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    await write_aes_128(dut, 0x00, FIPS197_KEY)
    await write_aes_128(dut, 0x20, FIPS197_PT)
    await write_aes_csr(dut, 0x40, 0)  # ECB encrypt
    await aes_trigger_start(dut)
    
    # Quickly issue second trigger while busy
    await Timer(50, units='ns')
    await write_aes_csr(dut, 0x44, 0x1)
    cocotb.log.info(f"Issued second trigger while busy")
    
    # Wait for first operation to complete
    await aes_wait_done(dut)
    result = await read_aes_128(dut, 0x30)
    
    assert result == FIPS197_CT, f"First operation corrupted: {result:#034x} vs {FIPS197_CT:#034x}"
    cocotb.log.info(f"✓ First operation completed correctly despite second trigger")
    cocotb.log.info(f"✓ VP-AES-015 PASS")
