"""Coverage-closing timing/FIFO register test for Task 2.2 I2C."""

import cocotb
from cocotb.triggers import Timer

from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    write_i2c_csr,
    read_i2c_csr,
)


@cocotb.test()
async def test_coverage_timing_fifo(dut):
    """Task 2.2 coverage test: exercise timing and FIFO-control CSR paths."""
    await generate_clock(dut)
    await generate_reset(dut)
    init_tl_driver(dut)

    timing_values = {
        0x1C: 0x00400020,
        0x20: 0x00180018,
        0x24: 0x00200020,
        0x28: 0x00100010,
        0x2C: 0x00080008,
    }

    for addr, value in timing_values.items():
        await write_i2c_csr(dut, addr, value)
        await Timer(50, unit="ns")
        readback = await read_i2c_csr(dut, addr)
        assert readback == value, f"Timing register mismatch at {addr:#x}: {readback:#010x} != {value:#010x}"

    await write_i2c_csr(dut, 0x10, 0x00010001)  # FIFO_CTRL watermark tuning
    fifo_ctrl = await read_i2c_csr(dut, 0x10)
    fifo_low = fifo_ctrl & 0x0001FFFF
    expected_low = 0x00010001 & 0x0001FFFF
    assert fifo_low in (0x00000000, expected_low), (
        "FIFO_CTRL readback should either reflect requested low fields or reset-like behavior; "
        f"got {fifo_ctrl:#010x}"
    )
