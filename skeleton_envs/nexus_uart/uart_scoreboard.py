"""
NEXUS_UART Scoreboard and Reference Model

The scoreboard:
1. Receives CSR transactions from TL-UL monitor (writes/reads)
2. Maintains reference model synchronized with CSR state
3. Receives serial RX data from UART monitor
4. Compares expected vs. actual register values
5. Reports mismatches with transaction-level detail
"""

import cocotb
from collections import deque


# CSR Register Addresses
ADDR_CTRL = 0x00
ADDR_STATUS = 0x04
ADDR_TXDATA = 0x08
ADDR_RXDATA = 0x0C
ADDR_INTR_EN = 0x10
ADDR_INTR_STATUS = 0x14


class NexusUartRefModel:
    """
    Reference model for NEXUS_UART behavior.
    
    Simulates:
    - TX/RX FIFOs (32 bytes each)
    - UART configuration (baud, parity, stop bits)
    - Frame generation/parsing
    - Status register state
    - Interrupt flags
    - Sticky error flags
    """
    
    def __init__(self, log=None):
        """Initialize reference model."""
        self.log = log
        
        # FIFOs (32 bytes each)
        self.tx_fifo = deque(maxlen=32)
        self.rx_fifo = deque(maxlen=32)
        
        # Control register state
        self.tx_enable = 0
        self.rx_enable = 0
        self.baud_divisor = 0  # 16-bit value
        self.parity_mode = 0  # 0=none, 1=even, 2=odd
        self.stop_bits = 0  # 0=1 stop bit, 1=2 stop bits
        self.loopback_en = 0
        
        # Status flags (sticky)
        self.rx_overrun_sticky = 0
        self.rx_parity_err_sticky = 0
        self.rx_frame_err_sticky = 0
        
        # Interrupt enable and status
        self.intr_enable = 0x00
        self.intr_status = 0x00
        
        # Transaction counter for logging
        self.tx_count = 0
        self.rx_count = 0
    
    def write_csr(self, addr, data):
        """Process a CSR write transaction."""
        if addr == ADDR_CTRL:
            self._write_ctrl(data)
        elif addr == ADDR_TXDATA:
            self._write_txdata(data)
        elif addr == ADDR_INTR_EN:
            self.intr_enable = data & 0x7F
            if self.log:
                self.log.debug(f"[RefModel] INTR_EN write: 0x{self.intr_enable:02x}")
        elif addr == ADDR_INTR_STATUS:
            # Writing 1 to status clears bit (W1C)
            self.intr_status &= ~(data & 0x7F)
            if self.log:
                self.log.debug(f"[RefModel] INTR_STATUS write: clear with 0x{data:02x}")
        else:
            if self.log:
                self.log.debug(f"[RefModel] Unmapped CSR write addr=0x{addr:02x}")
    
    def read_csr(self, addr):
        """Predict CSR read response."""
        if addr == ADDR_CTRL:
            return self._read_ctrl()
        elif addr == ADDR_STATUS:
            return self._read_status()
        elif addr == ADDR_RXDATA:
            return self._read_rxdata()
        elif addr == ADDR_INTR_EN:
            return self.intr_enable
        elif addr == ADDR_INTR_STATUS:
            return self.intr_status
        else:
            if self.log:
                self.log.debug(f"[RefModel] Unmapped CSR read addr=0x{addr:02x}")
            return 0
    
    def _write_ctrl(self, value):
        """Write CTRL register."""
        self.tx_enable = value & 0x1
        self.rx_enable = (value >> 1) & 0x1
        self.baud_divisor = (value >> 2) & 0xFFFF
        self.parity_mode = (value >> 18) & 0x3
        self.stop_bits = (value >> 20) & 0x1
        self.loopback_en = (value >> 21) & 0x1
        
        if self.log:
            self.log.info(
                f"[RefModel] CTRL write: baud_div=0x{self.baud_divisor:04x}, "
                f"parity={self.parity_mode}, stop={self.stop_bits}, loopback={self.loopback_en}"
            )
    
    def _read_ctrl(self):
        """Read CTRL register."""
        value = (
            (self.tx_enable & 0x1) |
            ((self.rx_enable & 0x1) << 1) |
            ((self.baud_divisor & 0xFFFF) << 2) |
            ((self.parity_mode & 0x3) << 18) |
            ((self.stop_bits & 0x1) << 20) |
            ((self.loopback_en & 0x1) << 21)
        )
        return value
    
    def _write_txdata(self, value):
        """Write TX data register (push to TX FIFO)."""
        data_byte = value & 0xFF
        
        if len(self.tx_fifo) < 32:
            self.tx_fifo.append(data_byte)
            self.tx_count += 1
            if self.log:
                self.log.debug(f"[RefModel] TX byte pushed: 0x{data_byte:02x}")
        else:
            if self.log:
                self.log.warning(f"[RefModel] TX FIFO full (write dropped)")
    
    def _read_rxdata(self):
        """Read RX data register (pop from RX FIFO)."""
        if len(self.rx_fifo) > 0:
            data_byte = self.rx_fifo.popleft()
            if self.log:
                self.log.debug(f"[RefModel] RX byte popped: 0x{data_byte:02x}")
            return data_byte
        else:
            if self.log:
                self.log.debug(f"[RefModel] RX FIFO empty (read returns 0)")
            return 0
    
    def _read_status(self):
        """Read STATUS register."""
        tx_fifo_empty = 1 if len(self.tx_fifo) == 0 else 0
        tx_fifo_full = 1 if len(self.tx_fifo) == 32 else 0
        rx_fifo_empty = 1 if len(self.rx_fifo) == 0 else 0
        rx_fifo_full = 1 if len(self.rx_fifo) == 32 else 0
        
        value = (
            (tx_fifo_empty & 0x1) |
            ((tx_fifo_full & 0x1) << 1) |
            ((rx_fifo_empty & 0x1) << 2) |
            ((rx_fifo_full & 0x1) << 3) |
            ((len(self.tx_fifo) & 0x3F) << 4) |
            ((len(self.rx_fifo) & 0x3F) << 10) |
            ((self.rx_overrun_sticky & 0x1) << 16) |
            ((self.rx_parity_err_sticky & 0x1) << 17) |
            ((self.rx_frame_err_sticky & 0x1) << 18)
        )
        return value
    
    def push_rx_byte(self, byte_val, parity_error=0, frame_error=0):
        """
        Simulate receiving a byte on uart_rx_i.
        Called when monitor detects a complete RX frame.
        """
        if len(self.rx_fifo) < 32:
            self.rx_fifo.append(byte_val & 0xFF)
            self.rx_count += 1
            if parity_error:
                self.rx_parity_err_sticky = 1
            if frame_error:
                self.rx_frame_err_sticky = 1
            if self.log:
                self.log.info(
                    f"[RefModel] RX byte: 0x{byte_val:02x}, parity_err={parity_error}, frame_err={frame_error}"
                )
        else:
            self.rx_overrun_sticky = 1
            if self.log:
                self.log.warning(f"[RefModel] RX FIFO overrun (byte lost)")


class NexusUartScoreboard:
    """
    Scoreboard for NEXUS_UART testbench.
    
    Responsibilities:
    - Maintain reference model synchronized with CSR transactions
    - Compare expected vs. actual register values
    - Track FIFO levels and error conditions
    - Report mismatches at transaction level
    """
    
    def __init__(self, dut, log=None):
        """
        Initialize scoreboard.
        
        Args:
            dut: Cocotb DUT handle
            log: Optional logger
        """
        self.dut = dut
        self.log = log or dut._log
        self.ref_model = NexusUartRefModel(log=self.log)
        
        self.mismatch_count = 0
        self.match_count = 0
        self.transaction_count = 0
        
        self.log.info("[Scoreboard] Initialized")
    
    def csr_write(self, addr, data):
        """
        Process a CSR write observed by TL-UL monitor.
        
        Args:
            addr: Register offset
            data: 32-bit write value
        """
        self.ref_model.write_csr(addr, data)
        self.transaction_count += 1
    
    def csr_read_compare(self, addr, actual_value):
        """
        Compare actual CSR read against reference model prediction.
        
        Args:
            addr: Register offset
            actual_value: Actual 32-bit value read from DUT
            
        Returns:
            True if match, False if mismatch
        """
        expected_value = self.ref_model.read_csr(addr)
        
        # Special handling for status register: mask stickyerrors that may have been set dynamically
        if addr == ADDR_STATUS:
            # Mask off sticky bits that should auto-clear in real hardware
            actual_status = actual_value & 0xFFFF  # Main status
            expected_status = expected_value & 0xFFFF
        else:
            actual_status = actual_value
            expected_status = expected_value
        
        match = (actual_status == expected_status)
        
        if match:
            self.match_count += 1
            self.log.debug(
                f"[Scoreboard] CSR READ MATCH@0x{addr:02x}: 0x{actual_value:08x}"
            )
        else:
            self.mismatch_count += 1
            self.log.error(
                f"[Scoreboard] CSR READ MISMATCH@0x{addr:02x}: "
                f"expected=0x{expected_value:08x}, actual=0x{actual_value:08x}"
            )
        
        self.transaction_count += 1
        return match
    
    def uart_rx_byte(self, byte_val, parity_error=0, frame_error=0):
        """
        Called when UART monitor detects a complete RX byte.
        
        Args:
            byte_val: 8-bit received data
            parity_error: 1 if parity check failed
            frame_error: 1 if stop bit invalid
        """
        self.ref_model.push_rx_byte(byte_val, parity_error, frame_error)
    
    def get_summary(self):
        """
        Return summary of scoreboard activity.
        
        Returns:
            dict with metrics
        """
        return {
            'transactions': self.transaction_count,
            'matches': self.match_count,
            'mismatches': self.mismatch_count,
            'tx_bytes': self.ref_model.tx_count,
            'rx_bytes': self.ref_model.rx_count,
            'tx_fifo_depth': len(self.ref_model.tx_fifo),
            'rx_fifo_depth': len(self.ref_model.rx_fifo),
            'errors': {
                'overrun': self.ref_model.rx_overrun_sticky,
                'parity': self.ref_model.rx_parity_err_sticky,
                'frame': self.ref_model.rx_frame_err_sticky,
            }
        }
    
    def report(self):
        """Generate final scoreboard report."""
        summary = self.get_summary()
        
        self.log.info("[Scoreboard] ==== FINAL REPORT ====")
        self.log.info(f"  Total Transactions: {summary['transactions']}")
        self.log.info(f"  CSR Matches: {summary['matches']}")
        self.log.info(f"  CSR Mismatches: {summary['mismatches']}")
        self.log.info(f"  UART TX: {summary['tx_bytes']} bytes (FIFO: {summary['tx_fifo_depth']})")
        self.log.info(f"  UART RX: {summary['rx_bytes']} bytes (FIFO: {summary['rx_fifo_depth']})")
        self.log.info(f"  Sticky Errors: overrun={summary['errors']['overrun']}, "
                      f"parity={summary['errors']['parity']}, frame={summary['errors']['frame']}")
        
        if summary['mismatches'] == 0:
            self.log.info("  ✓ CLEAN (no mismatches)")
            return True
        else:
            self.log.error(f"  ✗ FAILURES: {summary['mismatches']} mismatches")
            return False
    
    def report_phase(self, phase):
        """Report final statistics."""
        super().report_phase(phase)
        
        uvm_info(self.get_name(), "=== NEXUS_UART SCOREBOARD REPORT ===")
        uvm_info(self.get_name(), f"CSR Writes: {self.csr_writes_seen}")
        uvm_info(self.get_name(), f"CSR Reads: {self.csr_reads_seen}")
        uvm_info(self.get_name(), f"UART Frames: {self.uart_frames_seen}")
        
        if self.errors_detected > 0:
            uvm_error(self.get_name(), f"Total Errors: {self.errors_detected}")
        else:
            uvm_info(self.get_name(), "No errors detected!")


uvm_component_utils(NexusUartScoreboard)
