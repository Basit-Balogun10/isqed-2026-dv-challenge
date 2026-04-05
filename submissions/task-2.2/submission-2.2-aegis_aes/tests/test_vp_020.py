# mypy: disable-error-code=import-not-found
"""VP-AES-020: Interrupt functionality"""
import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    write_aes_128,
    write_aes_csr,
    read_aes_csr,
    aes_trigger_start,
    aes_wait_done,
    FIPS197_KEY,
    FIPS197_PT,
)


@cocotb.test()
async def test_vp_aes_020(dut):
    """
    Interrupt and INTR_TEST.

    Enable aes_done interrupt, trigger an operation, and verify
    intr_o asserts on completion.
    """
    # CSR addresses used by this interrupt-focused test.
    INTR_STATE_ADDR = 0x4C
    INTR_ENABLE_ADDR = 0x50
    INTR_TEST_ADDR = 0x54

    # Initialize clock and reset.
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)

    # Clear any stale interrupt and enable aes_done interrupt path.
    await write_aes_csr(dut, INTR_STATE_ADDR, 0x1)
    await write_aes_csr(dut, INTR_ENABLE_ADDR, 0x1)
    await Timer(20, unit="ns")
    assert int(dut.intr_o.value) == 0, "intr_o should start low after reset/clear"

    # Trigger a real AES completion event.
    await write_aes_128(dut, 0x00, FIPS197_KEY)
    await write_aes_128(dut, 0x20, FIPS197_PT)
    await write_aes_csr(dut, 0x40, 0)
    await aes_trigger_start(dut)
    done = await aes_wait_done(dut, max_us=100)
    assert done, "AES operation did not complete before timeout"

    intr_state = await read_aes_csr(dut, INTR_STATE_ADDR)
    assert (intr_state & 0x1) == 1, "INTR_STATE.aes_done should set on AES completion"
    assert (
        int(dut.intr_o.value) == 1
    ), "intr_o should assert when aes_done interrupt is enabled"

    # Clear done interrupt via W1C and verify interrupt deasserts.
    await write_aes_csr(dut, INTR_STATE_ADDR, 0x1)
    await Timer(20, unit="ns")
    intr_state_after_clear = await read_aes_csr(dut, INTR_STATE_ADDR)
    assert (
        intr_state_after_clear & 0x1
    ) == 0, "INTR_STATE.aes_done should clear on W1C"
    assert (
        int(dut.intr_o.value) == 0
    ), "intr_o should deassert after clearing INTR_STATE"

    # Inject interrupt via INTR_TEST and verify the same path asserts.
    await write_aes_csr(dut, INTR_TEST_ADDR, 0x1)
    await Timer(20, unit="ns")
    intr_state_after_test = await read_aes_csr(dut, INTR_STATE_ADDR)
    assert (
        intr_state_after_test & 0x1
    ) == 1, "INTR_TEST should set INTR_STATE.aes_done"
    assert int(dut.intr_o.value) == 1, "intr_o should assert after INTR_TEST injection"

    await write_aes_csr(dut, INTR_STATE_ADDR, 0x1)
    await Timer(20, unit="ns")
    final_intr_state = await read_aes_csr(dut, INTR_STATE_ADDR)
    assert (final_intr_state & 0x1) == 0, "Final INTR_STATE.aes_done clear failed"
    assert int(dut.intr_o.value) == 0, "intr_o should end low after final clear"

    cocotb.log.info("✓ Interrupt done + INTR_TEST path validated")
    cocotb.log.info(f"✓ VP-AES-020 PASS")
