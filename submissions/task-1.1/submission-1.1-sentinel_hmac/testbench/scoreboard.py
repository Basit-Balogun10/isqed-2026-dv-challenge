"""SENTINEL_HMAC CSR Scoreboard (Cocotb native, no UVM)."""


class HmacRefModel:
    """Reference model for sentinel_hmac."""
    
    def __init__(self, log=None):
        self.log = log
        self.key = [0] * 16  # 512-bit key
        self.data_in = [0] * 16
        self.digest = [0] * 8  # 256-bit digest
        self.ctrl = 0
        self.status = 0
    
    def write_csr(self, addr, data):
        if 0x00 <= addr < 0x40:
            idx = (addr - 0x00) >> 2
            self.key[idx & 15] = data
        elif 0x40 <= addr < 0x80:
            idx = (addr - 0x40) >> 2
            self.data_in[idx & 15] = data
        elif addr == 0x80:
            self.ctrl = data
    
    def read_csr(self, addr):
        if 0x00 <= addr < 0x40:
            idx = (addr - 0x00) >> 2
            return self.key[idx & 15]
        elif 0x40 <= addr < 0x80:
            idx = (addr - 0x40) >> 2
            return self.data_in[idx & 15]
        elif 0x80 <= addr < 0xa0:
            idx = (addr - 0x80) >> 2
            return self.digest[idx & 7]
        elif addr == 0xa0:
            return self.ctrl
        return 0


class HmacScoreboard:
    """Scoreboard for sentinel_hmac (Cocotb native)."""
    
    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or dut._log
        self.ref_model = HmacRefModel(log=self.log)
        self.csr_ops = 0
        self.errors = 0
        self.log.info("[HMAC Scoreboard] Initialized")
    
    def write_csr(self, addr, data):
        self.ref_model.write_csr(addr, data)
        self.csr_ops += 1
    
    def read_csr_compare(self, addr, actual_data):
        expected = self.ref_model.read_csr(addr)
        match = (expected == actual_data)
        
        if not match and addr < 0xa0:
            self.log.error(f"[HMAC SB] MISMATCH @0x{addr:04x}: exp=0x{expected:08x} actual=0x{actual_data:08x}")
            self.errors += 1
        
        self.csr_ops += 1
        return match
    
    def report(self):
        self.log.info(f"=== SENTINEL_HMAC SCOREBOARD === CSR Ops: {self.csr_ops}, Errors: {self.errors}")
        return self.errors == 0
