# mypy: disable-error-code=import-not-found
"""Task 1.4 assertion exercise test for sentinel_hmac."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

from testbench.tl_ul_agent import TlUlDriver


ADDR_CFG = 0x00
ADDR_CMD = 0x04
ADDR_STATUS = 0x08
ADDR_DIGEST0 = 0x30
ADDR_INTR_STATE = 0x58
ADDR_INTR_ENABLE = 0x5C
ADDR_INTR_TEST = 0x60
ADDR_MSG_FIFO = 0x64


async def apply_reset(dut, cycles=5):
    dut.rst_ni.value = 0
    for _ in range(cycles):
        await RisingEdge(dut.clk_i)
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)


@cocotb.test()
async def test_with_assertions(dut):
    """Drive SHA/HMAC control traffic to exercise assertion antecedents on clean RTL."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())

    drv = TlUlDriver(dut)
    drv.idle_a_channel()

    await apply_reset(dut)

    # Enable all interrupts and inject a software interrupt to exercise INTR paths.
    await drv.write_reg(ADDR_INTR_ENABLE, 0x7)
    await drv.write_reg(ADDR_INTR_TEST, 0x2)
    intr_state = await drv.read_reg(ADDR_INTR_STATE)
    assert (intr_state & 0x2) == 0x2, f"Expected INTR_TEST bit set, got {intr_state:#x}"
    await drv.write_reg(ADDR_INTR_STATE, 0x2)

    # Configure SHA-only mode and run a short message hash.
    await drv.write_reg(ADDR_CFG, 0x2)  # sha_en=1, hmac_en=0
    await drv.write_reg(ADDR_CMD, 0x1)  # hash_start

    await drv.write_reg(ADDR_MSG_FIFO, 0x01234567)
    await drv.write_reg(ADDR_MSG_FIFO, 0x89ABCDEF)

    await drv.write_reg(ADDR_CMD, 0x4)  # hash_stop

    done_seen = False
    for _ in range(3000):
        state = await drv.read_reg(ADDR_INTR_STATE)
        if (state & 0x1) != 0:
            done_seen = True
            break
        await RisingEdge(dut.clk_i)

    assert done_seen, "Timed out waiting for hmac_done interrupt"

    digest0 = await drv.read_reg(ADDR_DIGEST0)
    assert digest0 != 0, "Digest word should be non-zero after hash completion"

    # Clear done interrupt and verify status remains readable.
    await drv.write_reg(ADDR_INTR_STATE, 0x1)
    status = await drv.read_reg(ADDR_STATUS)
    dut._log.info(f"Final STATUS={status:#010x}, DIGEST0={digest0:#010x}")

    for _ in range(100):
        await RisingEdge(dut.clk_i)
