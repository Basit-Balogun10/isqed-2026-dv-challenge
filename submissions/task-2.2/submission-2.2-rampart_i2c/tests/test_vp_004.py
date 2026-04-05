# mypy: disable-error-code=import-not-found
"""
VP-I2C-004: Multi-byte Write

START, address (write), then transmit 4 data bytes (0xAA, 0xBB, 0xCC, 0xDD),
each with ACK from slave, then STOP.

Priority: high
Coverage Target: cp_multi_byte_write.four_bytes
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
async def test_vp_i2c_004(dut):
    """VP-I2C-004: Multi-byte write (4 bytes)"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info(
        "[VP-I2C-004] Multi-byte write: 4 data bytes (0xAA, 0xBB, 0xCC, 0xDD)"
    )

    # Initialize TL-UL driver
    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Ensure host is idle before starting
    await i2c_wait_host_idle(dut)

    # Issue START condition
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-004] START issued")

    # Send address byte (7-bit address 0x50, shifted left + write bit 0)
    addr_write = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_write)
    cocotb.log.info(f"[VP-I2C-004] Address (write): {addr_write:#04x}")

    # Send 4 data bytes: 0xAA, 0xBB, 0xCC, 0xDD
    data_bytes = [0xAA, 0xBB, 0xCC, 0xDD]
    for idx, data in enumerate(data_bytes):
        # Write data to TX FIFO
        await i2c_write_tx_fifo(dut, data)
        # Issue fmt command to transmit byte
        await i2c_fmt_write_byte(dut, 0x00)
        cocotb.log.info(f"[VP-I2C-004] Byte {idx+1}: {data:#04x}")
        await Timer(200, unit="ns")

    # Issue STOP condition
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-004] STOP issued")

    # Wait for host to complete
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-004] Host did not return to idle"

    # Read final status
    status = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-004] Final status: {status:#010x}")

    cocotb.log.info("[VP-I2C-004] ✓ PASS")
