"""
NEXUS_UART Verification Environment

Ties together:
- TL-UL agent for CSR access
- UART protocol drivers/monitors for serial operations
- Scoreboard for behavioral verification
"""

import sys
import os

# Add parent directory to path for importing tl_ul_agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tl_ul_agent import TlUlAgent, TlUlSequencer
from uart_protocol_agent import NexusUartTxDriver, NexusUartRxMonitor, UartConfig
from uart_scoreboard import NexusUartScoreboard


class NexusUartEnvironment(uvm_env):
    """
    Complete verification environment for nexus_uart.
    
    Components:
    - tl_ul_agent: Handles CSR register access via TL-UL bus
    - uart_tx_driver: Drives uart_tx_o serial pin
    - uart_rx_monitor: Monitors uart_rx_i serial pin
    - scoreboard: Compares DUT against reference model
    """
    
    def __init__(self, name="nexus_uart_env", parent=None):
        super().__init__(name, parent)
        
        # Components
        self.tl_agent = None
        self.uart_tx_driver = None
        self.uart_rx_monitor = None
        self.scoreboard = None
        
        # DUT reference (injected from test)
        self.dut = None
    
    def build_phase(self, phase):
        """Build all environment components."""
        super().build_phase(phase)
        
        self.tl_agent = TlUlAgent("tl_ul_agent", self)
        self.uart_tx_driver = NexusUartTxDriver("uart_tx_driver", self)
        self.uart_rx_monitor = NexusUartRxMonitor("uart_rx_monitor", self)
        self.scoreboard = NexusUartScoreboard("uart_scoreboard", self)
    
    def connect_phase(self, phase):
        """Connect components and analysis ports."""
        super().connect_phase(phase)
        
        # Inject DUT reference
        self.tl_agent.dut = self.dut
        self.uart_tx_driver.dut = self.dut
        self.uart_rx_monitor.dut = self.dut
        
        # Connect TL-UL monitor to scoreboard
        self.tl_agent.analysis_port.connect(
            self.scoreboard.tl_analysis_port
        )
        
        # Connect UART RX monitor to scoreboard
        # self.uart_rx_monitor.analysis_port.connect(
        #     self.scoreboard.uart_analysis_port
        # )
    
    def start_of_simulation_phase(self, phase):
        """Initialize environment at simulation start."""
        super().start_of_simulation_phase(phase)
        
        uvm_info(self.get_name(),
                "NEXUS_UART Verification Environment initialized")


uvm_component_utils(NexusUartEnvironment)
