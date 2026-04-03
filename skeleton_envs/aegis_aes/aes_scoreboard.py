"""AEGIS_AES CSR Scoreboard (Cocotb native, no UVM)."""


class AesRefModel:
    """Reference model for aegis_aes."""
    
    def __init__(self, log=None):
        self.log = log
        self.key_share0 = [0] * 8  # 256-bit key shares
        self.key_share1 = [0] * 8
        self.plaintext = [0] * 4
        self.ciphertext = [0] * 4
        self.ctrl = 0
        self.status = 0
    
    def write_csr(self, addr, data):
        if 0x00 <= addr < 0x20:
            idx = (addr - 0x00) >> 2
            self.key_share0[idx & 7] = data
        elif 0x20 <= addr < 0x40:
            idx = (addr - 0x20) >> 2
            self.key_share1[idx & 7] = data
        elif addr == 0x40:
            self.ctrl = data
    
    def read_csr(self, addr):
        if 0x00 <= addr < 0x20:
            idx = (addr - 0x00) >> 2
            return self.key_share0[idx & 7]
        elif 0x20 <= addr < 0x40:
            idx = (addr - 0x20) >> 2
            return self.key_share1[idx & 7]
        elif addr == 0x40:
            return self.ctrl
        return 0


class AesScoreboard:
    """Scoreboard for aegis_aes (Cocotb native)."""
    
    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or dut._log
        self.ref_model = AesRefModel(log=self.log)
        self.csr_ops = 0
        self.errors = 0
        self.log.info("[AES Scoreboard] Initialized")
    
    def write_csr(self, addr, data):
        self.ref_model.write_csr(addr, data)
        self.csr_ops += 1
    
    def read_csr_compare(self, addr, actual_data):
        expected = self.ref_model.read_csr(addr)
        match = (expected == actual_data)
        
        if not match:
            self.log.error(f"[AES SB] MISMATCH @0x{addr:04x}: exp=0x{expected:08x} actual=0x{actual_data:08x}")
            self.errors += 1
        
        self.csr_ops += 1
        return match
    
    def report(self):
        self.log.info(f"=== AEGIS_AES SCOREBOARD === CSR Ops: {self.csr_ops}, Errors: {self.errors}")
        return self.errors == 0
