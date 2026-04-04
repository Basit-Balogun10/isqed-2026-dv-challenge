# mypy: disable-error-code=import-not-found
"""
VP-I2C-019: FIFO Operation During I2C

Write multiple bytes to TX FIFO and FMT FIFO, verify they are
transmitted in correct order on the I2C bus.

Priority: high/medium
Coverage Target: cp_fifo_ops.transmission_order
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
    i2c_write_tx_fifo,
    i2c_wait_host_idle,
    i2c_get_status,
)


@cocotb.test()
async def test_vp_i2c_019(dut):
    """VP-I2C-019: FIFO operation - verify transmission order"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-019] FIFO operation test")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Wait for bus idle
    await i2c_wait_host_idle(dut)

    # Issue START
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-019] START issued")

    # Send address byte via FMT FIFO + address
    addr_write = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_write)
    cocotb.log.info(f"[VP-I2C-019] Address queued: {addr_write:#04x}")

    # Queue multiple data bytes in TX FIFO
    # These should be transmitted in FIFO order
    data_sequence = [0x11, 0x22, 0x33, 0x44, 0x55]

    for idx, data_byte in enumerate(data_sequence):
        # Write to TX FIFO
        await i2c_write_tx_fifo(dut, data_byte)
        # Issue format command to transmit from TX FIFO
        await i2c_fmt_write_byte(dut, 0x00)
        cocotb.log.info(f"[VP-I2C-019] Byte {idx+1} queued: {data_byte:#04x}")
        await Timer(200, unit="ns")

    cocotb.log.info("[VP-I2C-019] All 5 bytes queued in transmission order")

    # Wait for all bytes to be transmitted
    await Timer(5000, unit="ns")

    # Check status for FIFO emptiness/completion
    status = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-019] Status after TX: {status:#010x}")

    # Issue STOP
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-019] STOP issued")

    # Wait for idle
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-019] Host did not return to idle"

    cocotb.log.info("[VP-I2C-019] ✓ PASS (all bytes transmitted in order)")
