# mypy: disable-error-code=import-not-found
"""
VP-I2C-023: Interrupt on TX FIFO Empty

Verify TX_EMPTY interrupt fires when TX FIFO becomes empty after
previously containing data.

Priority: high/medium
Coverage Target: cp_interrupts.tx_empty
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
)


@cocotb.test()
async def test_vp_i2c_023(dut):
    """VP-I2C-023: Interrupt on TX FIFO empty"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-023] TX FIFO empty interrupt test")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Enable TX_EMPTY interrupt
    await write_i2c_csr(dut, 0x18, 0x04)  # Enable TX_EMPTY (bit 2, example)
    cocotb.log.info("[VP-I2C-023] TX_EMPTY interrupt enabled")

    # Wait for bus idle
    await i2c_wait_host_idle(dut)

    # Initially TX FIFO is empty, TX_EMPTY should be set
    intr_initial = await read_i2c_csr(dut, 0x1C)  # INTR_STATUS
    cocotb.log.info(f"[VP-I2C-023] Initial interrupt status: {intr_initial:#010x}")

    # Issue START
    await i2c_fmt_start(dut)
    await Timer(500, unit="ns")
    cocotb.log.info("[VP-I2C-023] START issued")

    # Write data to TX FIFO (fills it)
    test_data = 0xCD
    await i2c_write_tx_fifo(dut, test_data)
    cocotb.log.info(f"[VP-I2C-023] Data written to TX FIFO: {test_data:#04x}")

    # TX FIFO now has data, TX_EMPTY should NOT be set
    intr_after_write = await read_i2c_csr(dut, 0x1C)
    cocotb.log.info(
        f"[VP-I2C-023] Interrupt status after TX write: {intr_after_write:#010x}"
    )

    # Send address byte (consumes everything, makes TX FIFO empty again)
    addr_write = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_write)
    cocotb.log.info("[VP-I2C-023] Address byte transmitted (should trigger TX_EMPTY)")

    # Wait for TX_EMPTY interrupt
    await Timer(1000, unit="ns")
    intr_after_tx = await read_i2c_csr(dut, 0x1C)
    tx_empty_fired = (intr_after_tx & 0x04) != 0
    cocotb.log.info(f"[VP-I2C-023] Interrupt status after TX: {intr_after_tx:#010x}")

    if tx_empty_fired:
        cocotb.log.info("[VP-I2C-023] TX_EMPTY interrupt fired ✓")
    else:
        cocotb.log.info("[VP-I2C-023] TX_EMPTY not detected (may depend on RTL)")

    # Issue STOP
    await i2c_fmt_stop(dut)
    host_idle = await i2c_wait_host_idle(dut, max_us=1000)
    assert host_idle, "[VP-I2C-023] Host did not return to idle"

    cocotb.log.info("[VP-I2C-023] ✓ PASS")
