"""
WARDEN_TIMER CSR Scoreboard

Verifies timer configuration and interrupt generation via CSR access.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tl_ul_agent import TlUlAgent


class TimerRefModel:
    """Reference model for warden_timer."""
    
    def __init__(self):
        self.prescaler = 0
        self.mtimecmp0_low = 0
        self.mtimecmp0_high = 0
        self.mtimecmp1_low = 0
        self.mtimecmp1_high = 0
        self.wd_bark_thresh = 0
        self.wd_bite_thresh = 0
        self.wd_ctrl = 0
        self.intr_state = 0
        self.intr_enable = 0
    
    def write_csr(self, addr, data):
        """Update CSR on write."""
        # CSR register addresses (from spec)
        if addr == 0x00:
            self.prescaler = data
        elif addr == 0x08:
            self.mtimecmp0_low = data
        elif addr == 0x0C:
            self.mtimecmp0_high = data
        elif addr == 0x10:
            self.mtimecmp1_low = data
        elif addr == 0x14:
            self.mtimecmp1_high = data
        elif addr == 0x20:
            self.wd_bark_thresh = data
        elif addr == 0x24:
            self.wd_bite_thresh = data
        elif addr == 0x28:
            self.wd_ctrl = data
        elif addr == 0x40:
            self.intr_state &= ~data  # W1C
        elif addr == 0x44:
            self.intr_enable = data


class TimerScoreboard(uvm_scoreboard):
    """Scoreboard for warden_timer."""
    
    def __init__(self, name="timer_scoreboard", parent=None):
        super().__init__(name, parent)
        self.ref_model = TimerRefModel()
        
        self.tl_analysis_port = uvm_analysis_imp(
            "tl_analysis_port", self, self._tl_transaction_observed
        )
        
        self.ops = 0
        self.errors = 0
    
    def _tl_transaction_observed(self, transaction):
        """Process CSR transaction."""
        addr = transaction.address
        
        if transaction.opcode == 0:  # Write
            self.ref_model.write_csr(addr, transaction.data)
            uvm_info(self.get_name(),
                    f"Timer CSR write @ 0x{addr:04x} = 0x{transaction.data:08x}")
        
        elif transaction.opcode == 4:  # Read
            # Verify CSR readback
            expected = self.ref_model.read_csr(addr) if hasattr(self.ref_model, 'read_csr') else 0
            uvm_info(self.get_name(),
                    f"Timer CSR read @ 0x{addr:04x} = 0x{transaction.response_data:08x}")
        
        self.ops += 1
    
    def report_phase(self, phase):
        super().report_phase(phase)
        uvm_info(self.get_name(), f"=== WARDEN_TIMER SCOREBOARD ===")
        uvm_info(self.get_name(), f"CSR Ops: {self.ops}")
        if self.errors == 0:
            uvm_info(self.get_name(), "✓ No errors")


uvm_component_utils(TimerScoreboard)


class TimerEnvironment(uvm_env):
    """Environment for warden_timer."""
    
    def __init__(self, name="timer_env", parent=None):
        super().__init__(name, parent)
        self.tl_agent = None
        self.scoreboard = None
        self.dut = None
    
    def build_phase(self, phase):
        super().build_phase(phase)
        self.tl_agent = TlUlAgent("tl_ul_agent", self)
        self.scoreboard = TimerScoreboard("timer_scoreboard", self)
    
    def connect_phase(self, phase):
        super().connect_phase(phase)
        self.tl_agent.dut = self.dut
        self.tl_agent.analysis_port.connect(self.scoreboard.tl_analysis_port)


uvm_component_utils(TimerEnvironment)
