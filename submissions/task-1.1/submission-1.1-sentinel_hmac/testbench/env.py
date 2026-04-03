"""
HMAC Verification Environment (sentinel_hmac)

Top-level environment that orchestrates the verification testbench:
  - TL-UL bus agent (CSR access)
  - Scoreboard (reference model, transaction tracking)
  - Coverage collection
"""

import cocotb
from tl_ul_agent import TlUlDriver, TlUlSeqItem
from scoreboard import HmacRefModel, HmacScoreboard


class HmacEnv:
    """HMAC verification environment."""

    def __init__(self, dut, log=None):
        """Initialize environment.
        
        Args:
            dut: DUT instance
            log: Optional logger
        """
        self.dut = dut
        self.log = log or dut._log
        self.tl_driver = TlUlDriver(dut, log=self.log)
        self.ref_model = HmacRefModel()
        self.scoreboard = HmacScoreboard(self.ref_model, log=self.log)

    async def setup_reset(self, duration=10):
        """Reset DUT and initialize.
        
        Args:
            duration: Reset duration in clock cycles
        """
        self.dut.rst_ni.value = 0
        for _ in range(duration):
            await cocotb.triggers.RisingEdge(self.dut.clk_i)
        self.dut.rst_ni.value = 1
        await cocotb.triggers.RisingEdge(self.dut.clk_i)
        self.log.info("[HmacEnv] Reset complete")

    async def write_csr(self, addr, value):
        """Write CSR register.
        
        Args:
            addr: Register address
            value: Data to write
        """
        item = TlUlSeqItem(opcode=1, address=addr, data=value, mask=0xF)
        await self.tl_driver.drive_seq_item(item)
        self.ref_model.csr_write(addr, value)
        self.scoreboard.record_write(addr, value)

    async def read_csr(self, addr):
        """Read CSR register.
        
        Args:
            addr: Register address
            
        Returns:
            Data read from register
        """
        item = TlUlSeqItem(opcode=4, address=addr, data=0, mask=0xF)
        await self.tl_driver.drive_seq_item(item)
        rdata = self.ref_model.predict_read(addr)
        self.scoreboard.record_read(addr, rdata)
        return rdata

    def report(self):
        """Print environment report."""
        self.scoreboard.report()
