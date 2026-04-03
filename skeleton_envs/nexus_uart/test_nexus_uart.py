"""
NEXUS_UART Cocotb Test Suite (Pure Cocotb, No UVM)

Tests basic UART CSR operations and protocol behavior.
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tl_ul_agent.tl_ul_driver import TlUlDriver
from uart_scoreboard import NexusUartScoreboard


class NexusUartEnv:
    """Minimal environment for UART verification."""
    
    def __init__(self, dut):
        self.dut = dut
        self.tl_ul = TlUlDriver(dut)
        self.scoreboard = NexusUartScoreboard(dut)
        self.log = dut._log
    
    async def setup_reset(self):
        """Reset DUT."""
        self.dut.rst_ni.value = 0
        await Timer(100, "ns")
        self.dut.rst_ni.value = 1
        await RisingEdge(self.dut.clk_i)
        self.log.info("[UART-ENV] Reset complete")
    
    async def write_csr(self, addr, data):
        """Write CSR via TL-UL."""
        await self.tl_ul.write_csr(addr, data)
        self.scoreboard.write_csr(addr, data)
    
    async def read_csr(self, addr):
        """Read CSR via TL-UL."""
        data = await self.tl_ul.read_csr(addr)
        self.scoreboard.read_csr_compare(addr, data)
        return data


@cocotb.test()
async def test_uart_ctrl_write_read(dut):
    """Test CTRL register write and read."""
    # Setup clock
    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    
    env = NexusUartEnv(dut)
    await env.setup_reset()
    
    # Write CTRL: enable TX/RX, baud divisor 16
    ctrl_val = 0x00000632  # [1:0]=11b (enable), [17:2]=16 (baud)
    await env.write_csr(0x00, ctrl_val)
    
    # Read back
    read_val = await env.read_csr(0x00)
    
    assert read_val == ctrl_val, f"CTRL mismatch: got 0x{read_val:08x}, exp 0x{ctrl_val:08x}"
    
    env.scoreboard.report()
    dut._log.info("[TEST] ✓ test_uart_ctrl_write_read PASSED")


@cocotb.test()
async def test_uart_status_empty(dut):
    """Test STATUS register (empty state)."""
    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    
    env = NexusUartEnv(dut)
    await env.setup_reset()
    
    # Read status - should show TX and RX empty
    status = await env.read_csr(0x04)
    
    tx_empty = (status >> 0) & 0x1
    rx_empty = (status >> 2) & 0x1
    
    dut._log.info(f"[TEST] STATUS: tx_empty={tx_empty}, rx_empty={rx_empty}")
    
    assert tx_empty == 1, "TX FIFO should be empty initially"
    assert rx_empty == 1, "RX FIFO should be empty initially"
    
    env.scoreboard.report()
    dut._log.info("[TEST] ✓ test_uart_status_empty PASSED")


@cocotb.test()
async def test_uart_txdata_write(dut):
    """Test TXDATA writes."""
    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    
    env = NexusUartEnv(dut)
    await env.setup_reset()
    
    # Write 4 bytes to TX FIFO
    test_bytes = [0x42, 0x55, 0xAA, 0xFF]
    for byte_val in test_bytes:
        await env.write_csr(0x08, byte_val)
    
    # Read STATUS
    status = await env.read_csr(0x04)
    
    tx_level = (status >> 4) & 0x3F
    dut._log.info(f"[TEST] TX FIFO level: {tx_level}")
    
    assert tx_level >= len(test_bytes), f"Expected FIFO >= {len(test_bytes)}, got {tx_level}"
    
    env.scoreboard.report()
    dut._log.info("[TEST] ✓ test_uart_txdata_write PASSED")

