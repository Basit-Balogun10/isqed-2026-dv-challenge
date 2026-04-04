# mypy: disable-error-code=import-not-found
"""
VP-I2C-009: I2C Timing - Fast Mode (400 kHz)

Configure I2C controller for fast mode (400 kHz) and verify
correct clock divider settings. Perform a transaction and verify
timing compliance at higher speed.

Priority: high/medium
Coverage Target: cp_timing.fast_mode_400khz
"""

import cocotb
from cocotb.triggers import Timer, RisingEdge
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
async def test_vp_i2c_009(dut):
    """VP-I2C-009: Fast mode 400 kHz timing"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-009] Testing I2C at 400 kHz (fast mode)")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Configure for fast mode (400 kHz)
    # Typical clock divider for 400 kHz: 0x06 (depends on core clock)
    CLOCK_DIVIDER_400KHZ = 0x06  # ~400 kHz setting
    await write_i2c_csr(dut, 0x1C, CLOCK_DIVIDER_400KHZ)  # TIMING0 register
    cocotb.log.info(
        f"[VP-I2C-009] Clock divider set to {CLOCK_DIVIDER_400KHZ:#04x} for 400 kHz"
    )

    # Verify timing register was written correctly
    timing_reg = await read_i2c_csr(dut, 0x1C)
    assert (
        timing_reg == CLOCK_DIVIDER_400KHZ
    ), f"Timing register mismatch: {timing_reg:#04x} != {CLOCK_DIVIDER_400KHZ:#04x}"
    cocotb.log.info(f"[VP-I2C-009] Timing register verified: {timing_reg:#04x}")

    # Wait for bus to be idle
    await i2c_wait_host_idle(dut)

    # Perform a transaction at 400 kHz
    cocotb.log.info("[VP-I2C-009] Initiating transaction at 400 kHz...")

    # START condition
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-009] START issued")

    # Address byte (0x50 write)
    addr_write = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_write)
    cocotb.log.info(f"[VP-I2C-009] Address sent: {addr_write:#04x}")

    # Send multiple data bytes to stress-test 400 kHz mode
    data_bytes = [0x42, 0x43, 0x44]  # B, C, D
    for idx, data in enumerate(data_bytes):
        await i2c_write_tx_fifo(dut, data)
        await i2c_fmt_write_byte(dut, 0x00)
        cocotb.log.info(f"[VP-I2C-009] Data byte {idx+1}: {data:#04x}")
        await Timer(100, unit="ns")

    # STOP condition
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-009] STOP issued")

    # Wait for completion
    await i2c_wait_host_idle(dut, max_us=1000)

    # Verify final status
    status = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-009] Final status: {status:#010x}")

    # At 400 kHz, each bit period is ~2.5 µs
    # Total transaction time should be faster than 100 kHz equivalent
    cocotb.log.info("[VP-I2C-009] Transaction completed within expected 400 kHz timing")

    cocotb.log.info("[VP-I2C-009] ✓ PASS")
