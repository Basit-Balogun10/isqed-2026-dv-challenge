"""
I2C Environment Integration Module - Complete Wrapper

Coordinates TL-UL agent, I2C protocol driver/monitor, and scoreboard
for end-to-end I2C testbench execution.
"""

import cocotb
from cocotb.triggers import RisingEdge


class I2cTestEnvironment:
    """Complete I2C test environment for RAMPART_I2C."""

    def __init__(self, dut, tl_ul_agent):
        """Initialize complete I2C test environment."""
        self.dut = dut
        self.tl_ul_agent = tl_ul_agent
        self.log = dut._log

        from .coverage import I2cCoverageModel
        from .i2c_protocol_agent import I2cProtocolAgent, I2cConfig
        from .i2c_scoreboard import I2cEnvironment

        # Required by Task 1.1 spec: env must instantiate a coverage collector.
        self.coverage = I2cCoverageModel(log=self.log)

        # Protocol agent (driver + monitor)
        i2c_config = I2cConfig(speed_mode="standard", target_address=0x50, is_host=True)
        self.i2c_protocol_agent = I2cProtocolAgent(dut, i2c_config)

        # Full environment (TL-UL + protocol + scoreboard)
        self.i2c_env = I2cEnvironment(dut, tl_ul_agent)

    async def start(self):
        """Start all background monitors."""
        await self.i2c_env.start()
        self.log.info("I2C Test Environment fully initialized")

    async def reset(self):
        """Reset DUT and clear FIFOs."""
        self.dut.rst_ni.value = 0
        await RisingEdge(self.dut.clk_i)
        await RisingEdge(self.dut.clk_i)
        self.dut.rst_ni.value = 1
        await RisingEdge(self.dut.clk_i)
        self.log.info("I2C DUT reset")

    async def enable_host_mode(self):
        """Enable I2C host (master) mode."""
        await self.i2c_env.write_csr(0x00, 0x01)  # CTRL: host_enable=1
        self.log.info("I2C host mode enabled")

    async def enable_target_mode(self):
        """Enable I2C target (slave) mode."""
        await self.i2c_env.write_csr(0x00, 0x02)  # CTRL: target_enable=1
        self.log.info("I2C target mode enabled")

    async def set_bus_speed(self, speed_mode: str):
        """
        Configure I2C bus speed via timing registers.

        Args:
            speed_mode (str): 'standard' (100 kHz), 'fast' (400 kHz), 'fastplus' (1 MHz)
        """
        # Simplified: Just update protocol agent config
        await self.i2c_protocol_agent.configure(speed_mode=speed_mode)
        self.log.info(f"I2C bus speed set to {speed_mode}")

    def report(self) -> dict:
        """Get test report from scoreboard."""
        self.coverage.report()
        return self.i2c_env.report()
