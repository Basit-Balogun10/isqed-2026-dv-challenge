"""RAMPART_I2C Cocotb Test Suite."""
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tl_ul_agent.tl_ul_driver import TlUlDriver
from i2c_scoreboard import I2cScoreboard

@cocotb.test()
async def test_i2c_ctrl_write(dut):
    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    dut.rst_ni.value = 0
    await Timer(100, "ns")
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)
    
    tl_ul = TlUlDriver(dut)
    sb = I2cScoreboard(dut)
    
    ctrl_val = 0x00000001
    await tl_ul.write_csr(0x00, ctrl_val)
    sb.write_csr(0x00, ctrl_val)
    read_val = await tl_ul.read_csr(0x00)
    sb.read_csr_compare(0x00, read_val)
    assert read_val == ctrl_val
    
    sb.report()
    dut._log.info("[TEST] ✓ test_i2c_ctrl_write PASSED")
