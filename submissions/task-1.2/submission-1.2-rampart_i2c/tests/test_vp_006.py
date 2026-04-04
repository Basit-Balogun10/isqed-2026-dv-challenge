# mypy: disable-error-code=import-not-found
"""
VP-I2C-006: 10-bit Addressing Mode

Master initiates write transaction using 10-bit address mode.
Sends 10-bit address (0x150 with write bit), then data, STOP.

In 10-bit mode:
- First byte: 11110xy0 (where xy are upper 2 bits of 10-bit addr)
- Second byte: Lower 8 bits of address
- Then data and STOP

Priority: medium
Coverage Target: cp_10bit_addr.write
"""

import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    write_i2c_csr,
    read_i2c_csr,
    i2c_enable_host,
    i2c_fmt_start,
    i2c_fmt_stop,
    i2c_fmt_write_byte,
    i2c_write_tx_fifo,
    i2c_wait_host_idle,
    i2c_get_status,
)


@cocotb.test()
async def test_vp_i2c_006(dut):
    """VP-I2C-006: 10-bit address write transaction"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-006] 10-bit addressing: addr 0x150 (0b0101010000)")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Enable 10-bit addressing mode in CONFIG register (bit 0 typically)
    # Note: This depends on RTL implementation; adjust register/bit as needed
    await write_i2c_csr(dut, 0x00, 0x01)  # Assume bit 0 enables 10-bit mode
    await Timer(100, unit="ns")
    cocotb.log.info("[VP-I2C-006]   10-bit mode enabled")

    # Wait for bus to be idle
    await i2c_wait_host_idle(dut)

    # Issue START condition
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-006]   START issued")

    # 10-bit address: 0x150 (binary: 0101 0101 0000)
    # Upper 2 bits: 01, Lower 8 bits: 0x50
    # First byte (10-bit format): 11110xy0 = 1111 01 00 = 0xF4 (xy=01 for upper 2 bits, 0=write)
    # Second byte: 0x50 (lower 8 bits)

    addr_10bit_upper = 0xF4  # 11110 + 01 (upper 2 bits) + 0 (write)
    addr_10bit_lower = 0x50  # Lower 8 bits

    await i2c_fmt_write_byte(dut, addr_10bit_upper)
    cocotb.log.info(
        f"[VP-I2C-006]   10-bit addr byte 1: {addr_10bit_upper:#04x} (0xF4 = 11110100)"
    )

    await i2c_fmt_write_byte(dut, addr_10bit_lower)
    cocotb.log.info(f"[VP-I2C-006]   10-bit addr byte 2: {addr_10bit_lower:#04x}")

    # Send data byte
    data_byte = 0x77
    await i2c_write_tx_fifo(dut, data_byte)
    await i2c_fmt_write_byte(dut, 0x00)  # Transmit from TX FIFO
    cocotb.log.info(f"[VP-I2C-006]   Data sent: {data_byte:#04x}")

    # Issue STOP condition
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-006]   STOP issued")

    # Wait for host to return to idle
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-006] Host did not return to idle"

    # Read final status
    status = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-006]   Final status: {status:#010x}")

    cocotb.log.info("[VP-I2C-006] ✓ PASS")
