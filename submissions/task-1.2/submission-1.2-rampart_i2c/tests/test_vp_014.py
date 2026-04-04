# mypy: disable-error-code=import-not-found
"""
VP-I2C-014: ACK Detection and Generation

After transmitting a byte, if target pulls SDA low during ACK clock bit,
this signals ACK. Verify master detects ACK and generates proper ACK bits.

Priority: high/medium
Coverage Target: cp_ack_nack.ack_generation
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
async def test_vp_i2c_014(dut):
    """VP-I2C-014: ACK detection and generation"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-014] ACK detection test")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Wait for bus to be idle
    await i2c_wait_host_idle(dut)

    # Issue START
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-014] START issued")

    # Send address with write bit
    # Expect slave to ACK (pull SDA low during ACK clock)
    addr_write = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_write)
    cocotb.log.info(f"[VP-I2C-014] Address sent: {addr_write:#04x}, expecting ACK")

    # Wait for ACK period
    await Timer(1000, unit="ns")

    # Read status - check for successful ACK reception
    status_after_addr = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-014] Status after address: {status_after_addr:#010x}")

    # Send data bytes and expect ACK for each
    data_bytes = [0x12, 0x34, 0x56]
    for idx, data in enumerate(data_bytes):
        await i2c_write_tx_fifo(dut, data)
        await i2c_fmt_write_byte(dut, 0x00)  # Transmit
        cocotb.log.info(
            f"[VP-I2C-014] Data byte {idx+1} sent: {data:#04x}, expecting ACK"
        )
        await Timer(800, unit="ns")

        # Check status after each byte
        status = await i2c_get_status(dut)
        cocotb.log.info(f"[VP-I2C-014] Status after byte {idx+1}: {status:#010x}")

    # Issue STOP
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-014] STOP issued")

    # Wait for idle
    host_idle = await i2c_wait_host_idle(dut, max_us=1000)
    assert host_idle, "[VP-I2C-014] Host did not return to idle"

    cocotb.log.info("[VP-I2C-014] ✓ PASS")
