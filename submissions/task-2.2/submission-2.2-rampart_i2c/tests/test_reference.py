"""Reference baseline smoke test for Task 2.2 I2C submission."""

import cocotb
from cocotb.triggers import Timer

from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    i2c_enable_host,
    i2c_get_status,
)


@cocotb.test()
async def test_reference(dut):
    """Task 2.2 reference test: host enable and idle-state baseline."""
    await generate_clock(dut)
    await generate_reset(dut)
    init_tl_driver(dut)

    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    status = await i2c_get_status(dut)
    host_idle = (status >> 6) & 0x1
    assert host_idle == 1, f"Host should remain idle with no transfer queued, STATUS={status:#010x}"
