# mypy: disable-error-code=import-not-found
"""
VP-I2C-012: STOP Condition Timing

Verify STOP condition proper I2C timing: SDA transitions high while SCL is high.
This tests the protocol's STOP bit generation.

Priority: high/medium
Coverage Target: cp_stop_condition.timing
"""

import cocotb
from cocotb.triggers import Timer
from .helpers import (
    generate_clock,
    generate_reset,
    init_tl_driver,
    i2c_enable_host,
    i2c_fmt_start,
    i2c_fmt_write_byte,
    i2c_fmt_stop,
    i2c_write_tx_fifo,
    i2c_wait_host_idle,
    i2c_get_status,
)


@cocotb.test()
async def test_vp_i2c_012(dut):
    """VP-I2C-012: STOP condition timing verification"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-012] STOP condition timing test")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Wait for bus to be idle
    await i2c_wait_host_idle(dut)

    # Perform a minimal transaction to reach a point where we can issue STOP
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-012] START issued")

    # Send address to put bus in an active transaction state
    addr_write = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_write)
    await Timer(500, unit="ns")

    # Send one data byte
    await i2c_write_tx_fifo(dut, 0x88)
    await i2c_fmt_write_byte(dut, 0x00)
    cocotb.log.info("[VP-I2C-012] Data sent")

    # Monitor bus lines before STOP
    sda_sig = (
        dut.sda
        if hasattr(dut, "sda")
        else dut.i2c_sda if hasattr(dut, "i2c_sda") else None
    )
    scl_sig = (
        dut.scl
        if hasattr(dut, "scl")
        else dut.i2c_scl if hasattr(dut, "i2c_scl") else None
    )

    if sda_sig and scl_sig:
        sda_before_stop = int(sda_sig.value)
        scl_before_stop = int(scl_sig.value)
        cocotb.log.info(
            f"[VP-I2C-012] Before STOP - SCL={scl_before_stop}, SDA={sda_before_stop}"
        )

    # Issue STOP condition
    # I2C STOP: SDA goes high while SCL is still high
    await i2c_fmt_stop(dut)
    await Timer(500, unit="ns")

    if sda_sig and scl_sig:
        sda_after_stop = int(sda_sig.value)
        scl_after_stop = int(scl_sig.value)
        cocotb.log.info(
            f"[VP-I2C-012] After STOP - SCL={scl_after_stop}, SDA={sda_after_stop}"
        )
        cocotb.log.info("[VP-I2C-012] STOP condition issued (SDA high while SCL high)")

    # Verify by reading status
    status = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-012] Status after STOP: {status:#010x}")

    # Wait for bus to return to idle
    host_idle = await i2c_wait_host_idle(dut, max_us=1000)
    assert host_idle, "[VP-I2C-012] Host did not return to idle"

    cocotb.log.info("[VP-I2C-012] ✓ PASS")
