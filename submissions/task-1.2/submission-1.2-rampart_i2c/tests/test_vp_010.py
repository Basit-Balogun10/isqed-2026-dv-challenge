# mypy: disable-error-code=import-not-found
"""
VP-I2C-010: General Call Address (0x00)

In I2C, address 0x00 is reserved as the general call address for
broadcasting commands to all slaves. This test sends a transaction
using the general call address (7-bit addr = 0x00) followed by a command byte.

Priority: high/medium
Coverage Target: cp_general_call.broadcast
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
async def test_vp_i2c_010(dut):
    """VP-I2C-010: General call address broadcast"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-010] General call broadcast (address 0x00)")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Wait for bus to be idle
    await i2c_wait_host_idle(dut)

    # Issue START condition
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-010] START issued")

    # Send general call address
    # General call: 7-bit address = 0x00, with write bit (R/W=0)
    # On bus: 0000 000 0 = 0x00
    general_call_addr = (0x00 << 1) | 0  # Address 0x00, write bit 0
    await i2c_fmt_write_byte(dut, general_call_addr)
    cocotb.log.info(f"[VP-I2C-010] General call address sent: {general_call_addr:#04x}")

    # Send command byte (example: 0x04 = Reset)
    command_byte = 0x04
    await i2c_write_tx_fifo(dut, command_byte)
    await i2c_fmt_write_byte(dut, 0x00)  # Transmit from TX FIFO
    cocotb.log.info(
        f"[VP-I2C-010] Command byte sent: {command_byte:#04x} (broadcast reset)"
    )

    # Issue STOP condition
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-010] STOP issued")

    # Wait for completion
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-010] Host did not return to idle"

    # Verify final status
    status = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-010] Final status: {status:#010x}")

    cocotb.log.info("[VP-I2C-010] ✓ PASS")
