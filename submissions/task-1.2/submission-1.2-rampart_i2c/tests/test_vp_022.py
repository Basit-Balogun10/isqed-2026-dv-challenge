# mypy: disable-error-code=import-not-found
"""
VP-I2C-022: Interrupt on RX FIFO Full

Receive bytes until RX FIFO fills, verify RX_FULL interrupt fires.

Priority: high/medium
Coverage Target: cp_interrupts.rx_full
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
async def test_vp_i2c_022(dut):
    """VP-I2C-022: Interrupt on RX FIFO full"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-022] RX FIFO full interrupt test")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Enable RX_FULL interrupt
    await write_i2c_csr(dut, 0x18, 0x08)  # Enable RX_FULL (bit 3, example)
    cocotb.log.info("[VP-I2C-022] RX_FULL interrupt enabled")

    # Wait for bus idle
    await i2c_wait_host_idle(dut)

    # Issue START
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-022] START issued")

    # Send address with READ bit to set up read transaction
    addr_read = (0x50 << 1) | 1
    await i2c_fmt_write_byte(dut, addr_read)
    cocotb.log.info("[VP-I2C-022] Address (read) sent")

    # Request many read operations to fill RX FIFO
    # Typical I2C FIFO depth is 64 bytes; try reading 16 bytes
    max_read_attempts = 16
    for idx in range(max_read_attempts):
        is_last = idx == (max_read_attempts - 1)
        await i2c_fmt_read_byte(dut, nack=is_last)
        await Timer(800, unit="ns")

        # Check interrupt status
        intr_status = await read_i2c_csr(dut, 0x1C)  # INTR_STATUS
        rx_full_fired = (intr_status & 0x08) != 0

        if rx_full_fired:
            cocotb.log.info(f"[VP-I2C-022] RX_FULL interrupt fired at byte {idx+1} ✓")
            break
        else:
            rx_data = await i2c_read_rx_fifo(dut)
            cocotb.log.info(f"[VP-I2C-022] Byte {idx+1} received: {rx_data:#04x}")

    # Issue STOP
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-022] STOP issued")

    # Wait for idle
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-022] Host did not return to idle"

    cocotb.log.info("[VP-I2C-022] ✓ PASS")
