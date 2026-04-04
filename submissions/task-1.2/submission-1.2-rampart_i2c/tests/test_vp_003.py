# mypy: disable-error-code=import-not-found
"""
VP-I2C-003: Repeated START Condition

START, address+write, write data, repeated START, address+read, read data, STOP.
Tests the protocol capability to change direction without releasing the bus.

Priority: high
Coverage Target: cp_repeated_start.basic_rstart
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
    i2c_write_tx_fifo,
    i2c_read_rx_fifo,
    i2c_wait_host_idle,
    i2c_get_status,
)


@cocotb.test()
async def test_vp_i2c_003(dut):
    """VP-I2C-003: Repeated START (write then read without stop)"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-003] Repeated START: write then read")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, units="ns")
    cocotb.log.info(f"  Enabled I2C host mode")

    # Wait for idle
    await i2c_wait_host_idle(dut)

    # === PHASE 1: Write operation ===
    cocotb.log.info(f"  [PHASE 1] Initial START + Address(write) + Data")

    # START condition
    await i2c_fmt_start(dut)
    cocotb.log.info(f"    START issued")

    # Address with WRITE (R/W=0)
    addr_w = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_w)
    cocotb.log.info(f"    Address (write): {addr_w:#04x}")

    # Send one data byte
    await i2c_write_tx_fifo(dut, 0x11)
    await i2c_fmt_write_byte(dut, 0x00)  # Transmit from TX FIFO
    cocotb.log.info(f"    Data sent: 0x11")

    # === PHASE 2: Repeated START (non-STOP, then START again) ===
    cocotb.log.info(f"  [PHASE 2] Repeated START + Address(read) + Data")
    await Timer(200, units="ns")

    # Repeated START (START without prior STOP)
    await i2c_fmt_start(dut)
    cocotb.log.info(f"    Repeated START issued")

    # Address with READ (R/W=1)
    addr_r = (0x50 << 1) | 1
    await i2c_fmt_write_byte(dut, addr_r)
    cocotb.log.info(f"    Address (read): {addr_r:#04x}")

    # Read one byte with ACK
    await i2c_fmt_read_byte(dut, nack=False)
    cocotb.log.info(f"    Read requested with ACK")

    await Timer(500, units="ns")
    rx_data = await i2c_read_rx_fifo(dut)
    cocotb.log.info(f"    Data received: {rx_data:#04x}")

    # === PHASE 3: STOP ===
    await i2c_fmt_stop(dut)
    cocotb.log.info(f"  [PHASE 3] STOP issued")

    # Wait for idle
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-003] Host did not return to idle"

    status = await i2c_get_status(dut)
    cocotb.log.info(f"  Final status: {status:#010x}")

    cocotb.log.info("[VP-I2C-003] ✓ PASS")
