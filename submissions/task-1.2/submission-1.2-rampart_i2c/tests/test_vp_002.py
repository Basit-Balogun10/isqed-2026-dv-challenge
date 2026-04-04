# mypy: disable-error-code=import-not-found
"""
VP-I2C-002: Basic I2C Read Transaction

Master initiates START, sends slave address (0x50 with read bit),
reads one data byte with ACK, and issues STOP.

Priority: high
Coverage Target: cp_read_transaction.basic_one_byte
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
    i2c_fmt_read_byte,
    i2c_read_rx_fifo,
    i2c_wait_host_idle,
    i2c_get_status,
)


@cocotb.test()
async def test_vp_i2c_002(dut):
    """VP-I2C-002: Basic read transaction - START, ADDRESS (READ), READ_BYTE, STOP"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-002] Basic read: addr 0x50, read 1 byte with ACK")

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

    # 2. Send slave address (0x50) with READ (R/W=1)
    slave_addr = 0x50
    addr_byte = (slave_addr << 1) | 1  # R/W bit = 1 (read)
    await i2c_fmt_write_byte(dut, addr_byte)
    cocotb.log.info(
        f"  Sent address byte: {addr_byte:#04x} (addr=0x{slave_addr:02x}, read)"
    )

    # 3. Request to read one byte with ACK (nack=False means send ACK after read)
    await i2c_fmt_read_byte(dut, nack=False)
    cocotb.log.info(f"  Requested read with ACK")

    # Wait a bit for the read to complete
    await Timer(500, unit="ns")

    # Read the received byte from RX FIFO
    rx_data = await i2c_read_rx_fifo(dut)
    cocotb.log.info(f"  Received data: {rx_data:#04x}")

    # 4. Issue STOP condition
    await i2c_fmt_stop(dut)
    cocotb.log.info(f"  Issued STOP condition")

    # Wait for host to return to idle
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-002] Host did not return to idle"

    # Read final status
    status = await i2c_get_status(dut)
    cocotb.log.info(f"  Final status: {status:#010x}")

    cocotb.log.info("[VP-I2C-002] ✓ PASS")
