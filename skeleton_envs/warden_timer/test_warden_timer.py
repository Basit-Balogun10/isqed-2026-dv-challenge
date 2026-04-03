"""WARDEN_TIMER Cocotb Test Suite."""
import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tl_ul_agent.tl_ul_driver import TlUlDriver
from timer_scoreboard import TimerScoreboard

@cocotb.test()
async def test_timer_prescaler_write(dut):
    cocotb.start_soon(Clock(dut.clk_i, 1, units="ns").start())
    dut.rst_ni.value = 0
    await Timer(100, "ns")
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)
    
    tl_ul = TlUlDriver(dut)
    sb = TimerScoreboard(dut)
    
    prescaler_val = 0x00000010
    await tl_ul.write_csr(0x00, prescaler_val)
    sb.write_csr(0x00, prescaler_val)
    read_val = await tl_ul.read_csr(0x00)
    sb.read_csr_compare(0x00, read_val)
    assert read_val == prescaler_val
    
    sb.report()
    dut._log.info("[TEST] ✓ test_timer_prescaler_write PASSED")
