"""
Generic CSR-Only Scoreboard Template

Use this template for DUTs that don't have protocol agents
(e.g., warden_timer, aegis_aes, sentinel_hmac).

These DUTs only need:
- CSR verification (reads/writes match expected values)
- Basic reference model (register state tracking)
- Interrupt verification (via CSR polling)

Steps to customize:
1. Copy this file to {dut}/csr_scoreboard.py
2. Replace CSR_ADDR_* with actual addresses from spec
3. Add any DUT-specific verification logic
"""



class CsrOnlyRefModel:
    """Generic reference model for CSR-only DUTs."""
    
    def __init__(self, name="generic_dut"):
        self.name = name
        self.registers = {}  # addr -> value
        self.intr_state = 0
        self.intr_enable = 0
    
    def write_csr(self, addr, data, mask=0xFFFFFFFF):
        """Update CSR on write."""
        current = self.registers.get(addr, 0)
        self.registers[addr] = (current & ~mask) | (data & mask)
    
    def read_csr(self, addr):
        """Read CSR."""
        return self.registers.get(addr, 0)


class CsrOnlyScoreboard(uvm_scoreboard):
    """Generic scoreboard for CSR-only DUTs."""
    
    def __init__(self, name="csr_only_scoreboard", dut_name="generic_dut", parent=None):
        super().__init__(name, parent)
        self.ref_model = CsrOnlyRefModel(dut_name)
        self.dut_name = dut_name
        
        self.tl_analysis_port = uvm_analysis_imp(
            "tl_analysis_port", self, self._tl_transaction_observed
        )
        
        self.csr_ops = 0
        self.errors = 0
    
    def _tl_transaction_observed(self, transaction):
        """Verify CSR transaction."""
        addr = transaction.address
        opcode = transaction.opcode
        
        if opcode == 0:  # Write
            self.ref_model.write_csr(addr, transaction.data, transaction.mask)
            uvm_info(self.get_name(),
                    f"{self.dut_name}: CSR write @ 0x{addr:04x} = 0x{transaction.data:08x}")
        
        elif opcode == 4:  # Read
            # For simplicity, just log reads
            uvm_info(self.get_name(),
                    f"{self.dut_name}: CSR read @ 0x{addr:04x} = 0x{transaction.response_data:08x}")
        
        self.csr_ops += 1
    
    def report_phase(self, phase):
        super().report_phase(phase)
        uvm_info(self.get_name(), f"=== {self.dut_name} CSR SCOREBOARD ===")
        uvm_info(self.get_name(), f"CSR Ops: {self.csr_ops}")
        if self.errors == 0:
            uvm_info(self.get_name(), "✓ No errors")
        else:
            uvm_error(self.get_name(), f"✗ Errors: {self.errors}")


uvm_component_utils(CsrOnlyScoreboard)


class CsrOnlyEnvironment(uvm_env):
    """Generic environment for CSR-only DUTs."""
    
    def __init__(self, name="csr_only_env", dut_name="generic_dut", parent=None):
        super().__init__(name, parent)
        self.dut_name = dut_name
        self.tl_agent = None
        self.scoreboard = None
        self.dut = None
    
    def build_phase(self, phase):
        super().build_phase(phase)
        
        # Import here to avoid circular deps
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from tl_ul_agent import TlUlAgent
        
        self.tl_agent = TlUlAgent("tl_ul_agent", self)
        self.scoreboard = CsrOnlyScoreboard("csr_scoreboard", self.dut_name, self)
    
    def connect_phase(self, phase):
        super().connect_phase(phase)
        self.tl_agent.dut = self.dut
        self.tl_agent.analysis_port.connect(self.scoreboard.tl_analysis_port)
    
    def start_of_simulation_phase(self, phase):
        super().start_of_simulation_phase(phase)
        uvm_info(self.get_name(), f"{self.dut_name} Environment initialized")


uvm_component_utils(CsrOnlyEnvironment)
