"""
BASTION_GPIO Cocotb Test Suite

Tests GPIO CSR operations and pin transitions.
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tl_ul_agent.tl_ul_driver import TlUlDriver
from gpio_scoreboard import GpioScoreboard


class GpioEnv:
    def __init__(self, dut):
        self.dut = dut
        self.tl_ul = TlUlDriver(dut)
        self.scoreboard = GpioScoreboard(dut)
    
    async def setup_reset(self):
        self.dut.rst_ni.value = 0
        await Timer(100, "ns")
        self.dut.rst_ni.value = 1
        await RisingEdge(self.dut.clk_i)
    
    async def write_csr(self, addr, data):
        await self.tl_ul.write_csr(addr, data)
        self.scoreboard.write_csr(addr, data)
    
    async def read_csr(self, addr):
        data = await self.tl_ul.read_csr(addr)
        self.scoreboard.read_csr_compare(addr, data)
        return data


@cocotb.test()
async def test_gpio_dir_write(dut):
    """Test GPIO direction register."""
    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    
    env = GpioEnv(dut)
    await env.setup_reset()
    
    # Write direction: set pins 0-7 as outputs
    dir_val = 0x000000FF
    await env.write_csr(0x08, dir_val)
    
    # Read back
    read_val = await env.read_csr(0x08)
    assert read_val == dir_val, f"DIR mismatch: got 0x{read_val:08x}, exp 0x{dir_val:08x}"
    
    env.scoreboard.report()
    dut._log.info("[TEST] ✓ test_gpio_dir_write PASSED")


@cocotb.test()
async def test_gpio_output_write(dut):
    """Test GPIO output register."""
    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    
    env = GpioEnv(dut)
    await env.setup_reset()
    
    # Write output value
    out_val = 0x000F00F0
    await env.write_csr(0x00, out_val)
    
    # Read back
    read_val = await env.read_csr(0x00)
    assert read_val == out_val, f"OUT mismatch: got 0x{read_val:08x}, exp 0x{out_val:08x}"
    
    env.scoreboard.report()
    dut._log.info("[TEST] ✓ test_gpio_output_write PASSED")
