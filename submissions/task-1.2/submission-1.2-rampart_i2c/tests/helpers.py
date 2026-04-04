"""
Pytest helpers for I2C (rampart_i2c) tests.

Provides:
- Clock and reset generation
- TL-UL CSR read/write helpers (via reusable TlUlDriver)
- I2C-specific functions (format FIFO, data FIFO access)
- Status register utilities
"""

import sys

sys.path.insert(0, ".")

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge
from testbench.tl_ul_agent import TlUlDriver

# ============================================================================
# CLOCK & RESET GENERATION
# ============================================================================


async def generate_clock(dut, period_ns=10):
    """
    Start clock generation for the testbench.

    Args:
        dut: Cocotb DUT handle
        period_ns: Clock period in nanoseconds (default 10ns = 100 MHz)
    """
    clock = Clock(dut.clk_i, period_ns, unit="ns")
    cocotb.start_soon(clock.start())
    await Timer(50, unit="ns")  # Wait for clock to stabilize


async def generate_reset(dut, cycles=5):
    """
    Generate active-low reset pulse.

    Args:
        dut: Cocotb DUT handle
        cycles: Number of clock cycles to hold reset
    """
    dut.rst_ni.value = 0
    for _ in range(cycles):
        await RisingEdge(dut.clk_i)
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)


# ============================================================================
# TL-UL DRIVER INSTANCE (initialized in test setup)
# ============================================================================

_tl_driver = None


def init_tl_driver(dut):
    """Initialize the TL-UL driver for CSR access."""
    global _tl_driver
    _tl_driver = TlUlDriver(dut, clk_signal="clk_i")


# ============================================================================
# CSR HELPERS (delegated to TlUlDriver)
# ============================================================================


async def write_i2c_csr(dut, addr, data):
    """Write a 32-bit CSR register via TL-UL using TlUlDriver."""
    if _tl_driver is None:
        init_tl_driver(dut)
    await _tl_driver.write_reg(addr, data, mask=0xF, source=0)


async def read_i2c_csr(dut, addr):
    """Read a 32-bit CSR register via TL-UL using TlUlDriver."""
    if _tl_driver is None:
        init_tl_driver(dut)
    return await _tl_driver.read_reg(addr, source=0)


# ============================================================================
# I2C-SPECIFIC HELPERS
# ============================================================================


async def i2c_enable_host(dut):
    """Enable I2C host (master) mode."""
    await write_i2c_csr(dut, 0x00, 0x1)  # CTRL: host_enable=1
    await Timer(100, unit="ns")


async def i2c_enable_target(dut):
    """Enable I2C target (slave) mode."""
    await write_i2c_csr(dut, 0x00, 0x2)  # CTRL: target_enable=1
    await Timer(100, unit="ns")


async def i2c_write_fmt_fifo(dut, data):
    """Write to format FIFO (0x08)."""
    await write_i2c_csr(dut, 0x08, data)
    await Timer(50, unit="ns")


async def i2c_write_tx_fifo(dut, data):
    """Write to TX FIFO (0x0C)."""
    await write_i2c_csr(dut, 0x0C, data)
    await Timer(50, unit="ns")


async def i2c_read_rx_fifo(dut):
    """Read from RX FIFO (0x10)."""
    return await read_i2c_csr(dut, 0x10)


async def i2c_get_status(dut):
    """Read I2C status register (0x04)."""
    return await read_i2c_csr(dut, 0x04)


async def i2c_wait_host_idle(dut, max_us=1000):
    """Wait for host state machine to become idle."""
    for _ in range(max_us * 100):
        status = await i2c_get_status(dut)
        if (status & 0x40) != 0:  # host_idle bit
            return True
        await Timer(10, unit="ns")
    return False


async def i2c_wait_target_idle(dut, max_us=1000):
    """Wait for target state machine to become idle."""
    for _ in range(max_us * 100):
        status = await i2c_get_status(dut)
        if (status & 0x80) != 0:  # target_idle bit
            return True
        await Timer(10, unit="ns")
    return False


async def i2c_wait_bus_idle(dut, max_us=1000):
    """Wait for I2C bus to become idle."""
    for _ in range(max_us * 100):
        status = await i2c_get_status(dut)
        if (status & 0x100) == 0:  # bus_active bit cleared
            return True
        await Timer(10, unit="ns")
    return False


async def i2c_fmt_start(dut):
    """Issue START condition via format FIFO."""
    # FMT FIFO format: [start=1, stop=0, data=0]
    await i2c_write_fmt_fifo(dut, 0x100)
    await Timer(100, unit="ns")


async def i2c_fmt_stop(dut):
    """Issue STOP condition via format FIFO."""
    # FMT FIFO format: [start=0, stop=1, data=0]
    await i2c_write_fmt_fifo(dut, 0x200)
    await Timer(100, unit="ns")


async def i2c_fmt_write_byte(dut, byte_val):
    """Write a byte via format FIFO."""
    # FMT FIFO: [start=0, stop=0, data=byte_val]
    await i2c_write_fmt_fifo(dut, byte_val)
    await Timer(100, unit="ns")


async def i2c_fmt_read_byte(dut, nack=False):
    """Read a byte (request via format FIFO)."""
    # FMT FIFO: [start=0, stop=0, byte_not_ack=nack, data=0]
    fmt_data = (1 << 9) | (nack << 8)
    await i2c_write_fmt_fifo(dut, fmt_data)
    await Timer(100, unit="ns")
