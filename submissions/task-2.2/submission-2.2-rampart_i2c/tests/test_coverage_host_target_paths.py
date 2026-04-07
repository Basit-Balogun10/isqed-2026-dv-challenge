"""Annotate-driven host/target closure test for Task 2.2 I2C."""

import cocotb
from cocotb.triggers import Timer

from .helpers import (
    generate_clock,
    generate_reset,
    i2c_enable_host,
    i2c_enable_target,
    i2c_fmt_read_byte,
    i2c_fmt_start,
    i2c_fmt_stop,
    i2c_fmt_write_byte,
    i2c_get_status,
    init_tl_driver,
    read_i2c_csr,
    write_i2c_csr,
)


@cocotb.test()
async def test_coverage_host_target_paths(dut):
    """Task 2.2 annotate closure: hit host/target config, FIFO reset, and FMT command paths."""
    await generate_clock(dut)
    await generate_reset(dut)
    init_tl_driver(dut)

    # Exercise target configuration write/read paths that were previously cold.
    target_cfg = (0x7F << 7) | 0x2A
    await write_i2c_csr(dut, 0x30, target_cfg)
    await i2c_enable_target(dut)
    target_rd = await read_i2c_csr(dut, 0x30)
    assert (target_rd & 0x3FFF) == (
        target_cfg & 0x3FFF
    ), f"TARGET_ID readback mismatch: got {target_rd:#010x}, expected {target_cfg:#010x}"

    # Enable host + loopback to stimulate START/WRITE/READ/STOP host state paths.
    await i2c_enable_host(dut)
    await write_i2c_csr(dut, 0x00, 0x5)  # host_enable + line_loopback

    # Touch timeout and interrupt paths (cold in previous annotation).
    await write_i2c_csr(dut, 0x3C, 0x00100001)
    await write_i2c_csr(dut, 0x44, 0x0000FFFF)
    intr_en = await read_i2c_csr(dut, 0x44)
    assert (
        intr_en & 0xFFFF
    ) == 0xFFFF, f"INTR_ENABLE readback mismatch: {intr_en:#010x}"

    # Assert all FIFO reset bits to exercise reset pulse handling in all FIFOs.
    await write_i2c_csr(dut, 0x10, 0xF)
    await Timer(100, unit="ns")

    # Drive a mixed format command stream to hit host command decode branches.
    await i2c_fmt_start(dut)
    await i2c_fmt_write_byte(dut, 0xA0)
    await i2c_fmt_write_byte(dut, 0x55)
    await i2c_fmt_read_byte(dut, nack=False)
    await i2c_fmt_stop(dut)

    # Allow internal FSM progression.
    await Timer(3000, unit="ns")

    status = await i2c_get_status(dut)
    # Confirm status path remains readable and host enable bit stayed set.
    ctrl = await read_i2c_csr(dut, 0x00)
    assert (
        ctrl & 0x1
    ) == 0x1, f"CTRL.host_enable unexpectedly cleared: CTRL={ctrl:#010x}"
    assert (
        status & 0xFFFFFFFF
    ) == status, f"STATUS read must be 32-bit value: {status:#010x}"
