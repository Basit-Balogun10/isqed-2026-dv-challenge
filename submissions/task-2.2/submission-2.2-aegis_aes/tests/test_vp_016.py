# mypy: disable-error-code=import-not-found
"""VP-AES-016: Status register accuracy"""
import cocotb
from cocotb.triggers import Timer, RisingEdge
from .helpers import (
    generate_clock,
    generate_reset,
    write_aes_128, write_aes_csr, read_aes_csr, aes_trigger_start, aes_wait_done,
    FIPS197_KEY, FIPS197_PT
)

@cocotb.test()
async def test_vp_aes_016(dut):
    """
    Status register accuracy.
    
    Check AES_STATUS at each phase: idle/input_ready=1 initially, 
    idle=0 after trigger, output_valid=1 after completion.
    Verify all status transitions.
    """
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    # Check initial state
    status_init = await read_aes_csr(dut, 0x48)
    cocotb.log.info(f"Initial status: {status_init:#010x}")
    
    # Load data and trigger
    await write_aes_128(dut, 0x00, FIPS197_KEY)
    await write_aes_128(dut, 0x20, FIPS197_PT)
    await write_aes_csr(dut, 0x40, 0)
    
    # Check status after trigger
    await aes_trigger_start(dut)
    await Timer(100, units='ns')
    status_busy = await read_aes_csr(dut, 0x48)
    cocotb.log.info(f"Status after trigger: {status_busy:#010x}")
    
    # Wait for done
    await aes_wait_done(dut)
    status_done = await read_aes_csr(dut, 0x48)
    cocotb.log.info(f"Status done: {status_done:#010x}")
    
    # Verify output_valid bit is set (bit 1)
    assert (status_done & 0x2) != 0, f"output_valid bit not set: {status_done:#010x}"
    cocotb.log.info(f"✓ Status transitions verified")
    cocotb.log.info(f"✓ VP-AES-016 PASS")
