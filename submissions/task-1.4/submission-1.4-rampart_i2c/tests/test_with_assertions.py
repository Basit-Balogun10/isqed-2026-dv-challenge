# mypy: disable-error-code=import-not-found
"""Task 1.4 assertion exercise test for rampart_i2c.

This test intentionally drives representative CSR traffic and mode transitions
so assertion antecedents are exercised in a clean-RTL run.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

from testbench.tl_ul_agent import TlUlDriver


ADDR_CTRL = 0x00
ADDR_STATUS = 0x04
ADDR_FIFO_CTRL = 0x10
ADDR_FIFO_STATUS = 0x14
ADDR_INTR_STATE = 0x40
ADDR_INTR_ENABLE = 0x44
ADDR_INTR_TEST = 0x48


async def apply_reset(dut, cycles=5):
    dut.rst_ni.value = 0
    for _ in range(cycles):
        await RisingEdge(dut.clk_i)
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)


@cocotb.test()
async def test_with_assertions(dut):
    """Run a clean directed sequence that exercises protocol, functional and liveness checks."""
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())

    # Default bus state is idle high when externally pulled up.
    dut.scl_i.value = 1
    dut.sda_i.value = 1

    drv = TlUlDriver(dut)
    drv.idle_a_channel()

    await apply_reset(dut)

    # Basic status reads exercise TL Get/response path.
    status0 = await drv.read_reg(ADDR_STATUS)
    fifo0 = await drv.read_reg(ADDR_FIFO_STATUS)
    dut._log.info(f"Initial status={status0:#010x}, fifo_status={fifo0:#010x}")

    # Exercise interrupt enable/test/state flow.
    await drv.write_reg(ADDR_INTR_ENABLE, 0x0000_FFFF)
    await drv.write_reg(ADDR_INTR_TEST, 0x0000_00A5)
    await Timer(100, unit="ns")

    intr_state = await drv.read_reg(ADDR_INTR_STATE)
    assert (intr_state & 0x00A5) == 0x00A5, (
        f"Expected test interrupt bits to be set, got {intr_state:#010x}"
    )

    await drv.write_reg(ADDR_INTR_STATE, 0x0000_00A5)
    await Timer(100, unit="ns")
    intr_state_cleared = await drv.read_reg(ADDR_INTR_STATE)
    assert (intr_state_cleared & 0x00A5) == 0, (
        f"Expected W1C clear behavior, got {intr_state_cleared:#010x}"
    )

    # Enable host + target + loopback to exercise control-path assertions.
    await drv.write_reg(ADDR_CTRL, 0x0000_0007)

    # Drive a small host command stream to move host FSM out of IDLE.
    # FDATA encoding: bit8=start, bit9=stop, data in bits[7:0].
    await drv.write_reg(0x0C, (1 << 8) | 0xA0)  # START + address byte (write)
    await drv.write_reg(0x0C, (1 << 9) | 0x55)  # data + STOP

    # Toggle FIFO reset controls (self-clearing bits).
    await drv.write_reg(ADDR_FIFO_CTRL, 0xF)
    await Timer(200, unit="ns")

    # Read back status after activity.
    status1 = await drv.read_reg(ADDR_STATUS)
    fifo1 = await drv.read_reg(ADDR_FIFO_STATUS)
    dut._log.info(f"Final status={status1:#010x}, fifo_status={fifo1:#010x}")

    # Let bounded liveness properties observe completion conditions.
    for _ in range(200):
        await RisingEdge(dut.clk_i)
