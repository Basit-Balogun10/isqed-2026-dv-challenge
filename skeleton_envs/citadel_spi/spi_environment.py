"""
SPI Environment Integration Module - Complete Wrapper

Coordinates TL-UL agent, SPI protocol driver/monitor, and scoreboard
for end-to-end SPI testbench execution.
"""

import cocotb
from cocotb.triggers import RisingEdge


class SpiTestEnvironment:
    """Complete SPI test environment for CITADEL_SPI."""
    
    def __init__(self, dut, tl_ul_agent):
        """Initialize complete SPI test environment."""
        self.dut = dut
        self.tl_ul_agent = tl_ul_agent
        self.log = dut._log
        
        from .spi_protocol_agent import SpiProtocolAgent, SpiConfig
        from .spi_scoreboard import SpiEnvironment
        
        # Protocol agent (driver + monitor)
        spi_config = SpiConfig(cpol=0, cpha=0, clkdiv=0x04)
        self.spi_protocol_agent = SpiProtocolAgent(dut, spi_config)
        
        # Full environment (TL-UL + protocol + scoreboard)
        self.spi_env = SpiEnvironment(dut, tl_ul_agent)
    
    async def start(self):
        """Start all background monitors."""
        await self.spi_env.start()
        self.log.info("SPI Test Environment fully initialized")
    
    async def reset(self):
        """Reset DUT and clear FIFOs."""
        self.dut.rst_ni.value = 0
        await RisingEdge(self.dut.clk_i)
        await RisingEdge(self.dut.clk_i)
        self.dut.rst_ni.value = 1
        await RisingEdge(self.dut.clk_i)
        self.log.info("SPI DUT reset")
    
    async def configure_controller(self, cpol: int, cpha: int, clkdiv: int):
        """Configure SPI controller via CSRs."""
        config_val = (clkdiv << 2) | (cpha << 1) | cpol
        await self.spi_env.write_csr(0x10, config_val)  # CONFIGOPTS
        self.log.info(f"SPI controller configured: CPOL={cpol}, CPHA={cpha}, CLKDIV={clkdiv}")
    
    async def enable_controller(self):
        """Enable SPI host controller."""
        await self.spi_env.write_csr(0x00, 0x03)  # CTRL: SPIEN + OUTPUT_EN
        self.log.info("SPI controller enabled")
    
    def report(self) -> dict:
        """Get test report from scoreboard."""
        return self.spi_env.report()
