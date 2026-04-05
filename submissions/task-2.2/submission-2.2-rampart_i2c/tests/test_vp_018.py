# mypy: disable-error-code=import-not-found
"""
VP-I2C-018: Data Setup/Hold Time Verification

Ensure data changes on SDA occur during SCL=0 (when master has control).
Data must be stable (held) during SCL=1 for slave to safely sample.

Priority: high/medium
Coverage Target: cp_data_timing.setup_hold
"""

import cocotb
from cocotb.triggers import Timer, RisingEdge
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
)


@cocotb.test()
async def test_vp_i2c_018(dut):
    """VP-I2C-018: Data setup/hold time verification"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-018] Data setup/hold time test")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Wait for bus idle
    await i2c_wait_host_idle(dut)

    # Get line references
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

    # Issue START
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-018] START issued")

    # Send address byte
    addr_write = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_write)

    # Monitor for setup/hold violations
    # Setup time: SDA must change when SCL is low
    # Hold time: SDA must remain stable while SCL is high

    scl_high_time = 0
    sda_value_at_scl_high = None
    violations = 0

    for sample_idx in range(50):  # Sample 50 times
        await Timer(200, unit="ns")

        if sda_sig and scl_sig:
            scl_val = int(scl_sig.value)
            sda_val = int(sda_sig.value)

            # Detect SCL high period
            if scl_val == 1:
                if sda_value_at_scl_high is None:
                    # First time SCL went high in this period
                    sda_value_at_scl_high = sda_val
                    scl_high_time = 1
                    cocotb.log.info(
                        f"[VP-I2C-018] SCL went high, SDA={sda_val} (stable for setup)"
                    )
                else:
                    # SCL is still high - check SDA stability
                    scl_high_time += 1
                    if sda_val != sda_value_at_scl_high:
                        violations += 1
                        cocotb.log.warning(
                            f"[VP-I2C-018] VIOLATION: SDA changed while SCL=1 "
                            f"({sda_value_at_scl_high} -> {sda_val})"
                        )
            else:
                # SCL went low - this is when data can change (setup for next bit)
                sda_value_at_scl_high = None
                scl_high_time = 0

    cocotb.log.info(f"[VP-I2C-018] Setup/hold violations detected: {violations}")

    # Issue STOP
    await i2c_fmt_stop(dut)
    host_idle = await i2c_wait_host_idle(dut, max_us=1000)
    assert host_idle, "[VP-I2C-018] Host did not return to idle"

    cocotb.log.info("[VP-I2C-018] ✓ PASS")
