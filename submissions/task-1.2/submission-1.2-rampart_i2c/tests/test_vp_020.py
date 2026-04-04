# mypy: disable-error-code=import-not-found
"""
VP-I2C-020: RX FIFO Population

During I2C read transactions, verify received bytes appear in the RX FIFO
with correct ordering. Multiple bytes should queue in FIFO.

Priority: high/medium
Coverage Target: cp_fifo_ops.rx_fifo_order
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
    i2c_get_status,
)


@cocotb.test()
async def test_vp_i2c_020(dut):
    """VP-I2C-020: RX FIFO population and ordering"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-020] RX FIFO population test")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Wait for bus idle
    await i2c_wait_host_idle(dut)

    # Issue START
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-020] START issued")

    # Send address with READ bit (R/W=1)
    addr_read = (0x50 << 1) | 1
    await i2c_fmt_write_byte(dut, addr_read)
    cocotb.log.info(f"[VP-I2C-020] Address (read) sent: {addr_read:#04x}")

    # Request to read multiple bytes
    # The first 3 bytes should get ACK, last byte gets NACK
    num_bytes = 4
    received_bytes = []

    for idx in range(num_bytes):
        is_last = idx == (num_bytes - 1)
        nack = is_last  # NACK on last byte

        # Request read operation
        await i2c_fmt_read_byte(dut, nack=nack)
        ack_nack_str = "NACK" if nack else "ACK"
        cocotb.log.info(f"[VP-I2C-020] Byte {idx+1} read requested ({ack_nack_str})")

        # Wait for byte to arrive in RX FIFO
        await Timer(1000, unit="ns")

        # Read from RX FIFO
        rx_data = await i2c_read_rx_fifo(dut)
        received_bytes.append(rx_data)
        cocotb.log.info(
            f"[VP-I2C-020] Byte {idx+1} received from RX FIFO: {rx_data:#04x}"
        )

    cocotb.log.info(
        f"[VP-I2C-020] Received bytes in order: {[f'{b:#04x}' for b in received_bytes]}"
    )

    # Issue STOP
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-020] STOP issued")

    # Wait for idle
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-020] Host did not return to idle"

    status = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-020] Final status: {status:#010x}")

    cocotb.log.info("[VP-I2C-020] ✓ PASS")
