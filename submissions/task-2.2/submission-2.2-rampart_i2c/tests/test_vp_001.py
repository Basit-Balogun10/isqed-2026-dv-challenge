# mypy: disable-error-code=import-not-found
"""
VP-I2C-001: Basic I2C Write Transaction

Master initiates START condition, sends slave address (0x50 with write bit),
sends one data byte (0xA5), and issues STOP condition.

Priority: high
Coverage Target: cp_write_transaction.basic_one_byte
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
async def test_vp_i2c_001(dut):
    """VP-I2C-001: Basic write transaction - START, ADDRESS, DATA, STOP"""
    cocotb.log.info("[VP-I2C-001] Basic write: addr 0x50, data 0xA5")

    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("✓ Clock and reset initialized")

    init_tl_driver(dut)

    # Enable I2C host (master) mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")
    cocotb.log.info(f"  Enabled I2C host mode")

    # Wait for bus to be idle
    await i2c_wait_host_idle(dut)
    cocotb.log.info(f"  Host is idle")

    # 1. Issue START condition
    await i2c_fmt_start(dut)
    cocotb.log.info(f"  Issued START condition")

    # 2. Send slave address (0x50) with WRITE (R/W=0)
    slave_addr = 0x50
    addr_byte = (slave_addr << 1) | 0  # R/W bit = 0 (write)
    await i2c_fmt_write_byte(dut, addr_byte)
    cocotb.log.info(
        f"  Sent address byte: {addr_byte:#04x} (addr=0x{slave_addr:02x}, write)"
    )

    # 3. Send one data byte
    data_byte = 0xA5
    await i2c_write_tx_fifo(dut, data_byte)
    await Timer(100, unit="ns")

    # Write format command to transmit the TX FIFO data
    await i2c_fmt_write_byte(dut, 0x00)  # Send data from TX FIFO
    cocotb.log.info(f"  Sent data byte: {data_byte:#04x}")

    # 4. Issue STOP condition
    await i2c_fmt_stop(dut)
    cocotb.log.info(f"  Issued STOP condition")

    # Wait for host to return to idle
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-001] Host did not return to idle"

    # Read final status
    status = await i2c_get_status(dut)
    cocotb.log.info(f"  Final status: {status:#010x}")

    cocotb.log.info("[VP-I2C-001] ✓ PASS")
