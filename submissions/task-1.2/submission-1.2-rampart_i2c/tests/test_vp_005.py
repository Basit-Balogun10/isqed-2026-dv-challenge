# mypy: disable-error-code=import-not-found
"""
VP-I2C-005: Multi-byte Read

START, address (read), read 4 bytes with ACK after each except last (NACK), STOP.

Priority: high
Coverage Target: cp_multi_byte_read.four_bytes_nack_last
"""

import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    i2c_enable_host,
    i2c_fmt_start,
    i2c_fmt_stop,
    i2c_fmt_write_byte,
    i2c_fmt_read_byte,
    i2c_read_rx_fifo,
    i2c_wait_host_idle,
)


@cocotb.test()
async def test_vp_i2c_005(dut):
    """VP-I2C-005: Multi-byte read (4 bytes, last with NACK)"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-005] Multi-byte read: 4 bytes (NACK on last)")

    init_tl_driver(dut)
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")
    await i2c_wait_host_idle(dut)

    await i2c_fmt_start(dut)
    addr_r = (0x50 << 1) | 1
    await i2c_fmt_write_byte(dut, addr_r)
    cocotb.log.info(f"  Address (read): {addr_r:#04x}")

    for i in range(4):
        nack = i == 3  # NACK on last byte
        await i2c_fmt_read_byte(dut, nack=nack)
        await Timer(300, unit="ns")
        rx = await i2c_read_rx_fifo(dut)
        ack_nack = "NACK" if nack else "ACK"
        cocotb.log.info(f"  Byte {i+1}: {rx:#04x} ({ack_nack})")

    await i2c_fmt_stop(dut)
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-005] Host did not return to idle"
    cocotb.log.info("[VP-I2C-005] ✓ PASS")
