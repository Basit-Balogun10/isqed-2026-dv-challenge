# mypy: disable-error-code=import-not-found
"""
VP-I2C-025: Integration Test - Full I2C Transaction

Complete write + read cycle in single transaction:
1. START
2. Address with WRITE bit
3. Send multiple data bytes
4. Repeated START (P-START-P)
5. Address with READ bit
6. Receive multiple data bytes
7. STOP

This tests full I2C protocol sequence end-to-end.

Priority: high
Coverage Target: cp_integration.full_cycle
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
    i2c_write_tx_fifo,
    i2c_read_rx_fifo,
    i2c_wait_host_idle,
    i2c_get_status,
)


@cocotb.test()
async def test_vp_i2c_025(dut):
    """VP-I2C-025: Full integration test - write + read cycle"""
    # Initialize clock and reset
    await generate_clock(dut, period_ns=10)
    await generate_reset(dut, cycles=5)
    cocotb.log.info("[VP-I2C-025] ========== INTEGRATION TEST ==========")

    init_tl_driver(dut)

    # Enable I2C host mode
    await i2c_enable_host(dut)
    await Timer(200, unit="ns")

    # Wait for bus idle
    await i2c_wait_host_idle(dut)

    # ===== PHASE 1: WRITE TRANSACTION =====
    cocotb.log.info("[VP-I2C-025] PHASE 1: Write transaction (START + ADDR + DATA)")

    # Issue START
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-025]   START issued")

    # Send address with WRITE bit (0x50 write)
    addr_write = (0x50 << 1) | 0
    await i2c_fmt_write_byte(dut, addr_write)
    cocotb.log.info(f"[VP-I2C-025]   Address (write) sent: {addr_write:#04x}")

    # Send 2 data bytes on write
    write_data = [0x11, 0x22]
    for idx, data_byte in enumerate(write_data):
        await i2c_write_tx_fifo(dut, data_byte)
        await i2c_fmt_write_byte(dut, 0x00)
        cocotb.log.info(f"[VP-I2C-025]   Write data byte {idx+1}: {data_byte:#04x}")
        await Timer(200, unit="ns")

    # ===== PHASE 2: REPEATED START (P-START-P) =====
    cocotb.log.info("[VP-I2C-025] PHASE 2: Repeated START (without STOP)")

    # Issue another START without prior STOP (repeated START)
    await i2c_fmt_start(dut)
    cocotb.log.info("[VP-I2C-025]   Repeated START issued")

    # Send address with READ bit (0x50 read)
    addr_read = (0x50 << 1) | 1
    await i2c_fmt_write_byte(dut, addr_read)
    cocotb.log.info(f"[VP-I2C-025]   Address (read) sent: {addr_read:#04x}")

    # ===== PHASE 3: READ TRANSACTION =====
    cocotb.log.info("[VP-I2C-025] PHASE 3: Read transaction (receive DATA)")

    # Read 3 bytes (ACK on first 2, NACK on last)
    read_data = []
    read_count = 3

    for idx in range(read_count):
        is_last = idx == (read_count - 1)
        await i2c_fmt_read_byte(dut, nack=is_last)
        ack_nack_str = "NACK" if is_last else "ACK"
        cocotb.log.info(f"[VP-I2C-025]   Read byte {idx+1} requested ({ack_nack_str})")

        await Timer(1000, unit="ns")

        # Read from RX FIFO
        rx_byte = await i2c_read_rx_fifo(dut)
        read_data.append(rx_byte)
        cocotb.log.info(f"[VP-I2C-025]   Read byte {idx+1} received: {rx_byte:#04x}")

    # ===== PHASE 4: STOP =====
    cocotb.log.info("[VP-I2C-025] PHASE 4: STOP condition")

    # Issue STOP
    await i2c_fmt_stop(dut)
    cocotb.log.info("[VP-I2C-025]   STOP issued")

    # Wait for bus to return to idle
    host_idle = await i2c_wait_host_idle(dut, max_us=2000)
    assert host_idle, "[VP-I2C-025] Host did not return to idle"

    # Read final status
    final_status = await i2c_get_status(dut)
    cocotb.log.info(f"[VP-I2C-025]   Final status: {final_status:#010x}")

    # ===== SUMMARY =====
    cocotb.log.info("[VP-I2C-025] ========== TRANSACTION SUMMARY ==========")
    cocotb.log.info(f"[VP-I2C-025] Write phase: {len(write_data)} bytes written")
    cocotb.log.info(f"[VP-I2C-025] Read phase: {len(read_data)} bytes read")
    cocotb.log.info(f"[VP-I2C-025] Read data: {[f'{b:#04x}' for b in read_data]}")

    cocotb.log.info("[VP-I2C-025] ✓ PASS - Full I2C cycle completed successfully")
