"""
SPI Protocol Agent for CITADEL_SPI Host Controller Verification

This module implements a complete SPI protocol driver and monitor for the SPI host controller.
It provides bit-level timing control for SCLK generation, chip-select management, MOSI/MISO
shifting, and all 4 SPI modes (CPOL/CPHA combinations).

Key Concepts:
- CPOL (Clock Polarity): Determines SCLK idle state (0=low, 1=high)
- CPHA (Clock Phase): Determines when data is sampled relative to SCLK edges
  * CPHA=0: data driven on leading edge, sampled on leading edge
  * CPHA=1: data driven on leading edge, sampled on trailing edge
- Modes: (CPOL, CPHA) → (0,0), (0,1), (1,0), (1,1)
- MSB-first serial shifting: 0x53 transmitted as 0,1,0,1,0,0,1,1 on MOSI

Data paths:
- Transmit: TX FIFO → Shift Register → MOSI output
- Receive: MISO input → Shift Register → RX FIFO
"""

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class SpiConfig:
    """
    SPI configuration container for timing and mode settings.
    
    Attributes:
        clkdiv (int): 16-bit SCLK frequency divider. f_sclk = f_clk / (2 * (clkdiv + 1))
        cpol (int): Clock polarity (0=idle low, 1=idle high)
        cpha (int): Clock phase (0=sample on leading edge, 1=sample on trailing edge)
        csn_lead (int): Setup time in half-SCLK periods before first SCLK edge
        csn_trail (int): Hold time in half-SCLK periods after last SCLK edge
        csn_idle (int): Minimum inter-CS gap in half-SCLK periods
        csid (int): Active chip-select index (0-3)
        bit_period_cycles (int): Number of system clock cycles per SCLK half-period
    """
    clkdiv: int = 0x00
    cpol: int = 0
    cpha: int = 0
    csn_lead: int = 1
    csn_trail: int = 1
    csn_idle: int = 1
    csid: int = 0
    bit_period_cycles: Optional[int] = None
    
    def __post_init__(self):
        """Compute bit_period_cycles from clkdiv if not explicitly set."""
        if self.bit_period_cycles is None:
            # f_sclk = f_clk / (2 * (clkdiv + 1))
            # bit_period_cycles = 2 * (clkdiv + 1) system clock cycles per SCLK half period
            self.bit_period_cycles = 2 * (self.clkdiv + 1)


class SpiMasterDriver:
    """
    SPI Master (Host) Driver - Generates SPI protocol on MOSI/SCLK/CSN lines.
    
    This driver bit-bangs SPI transactions at the protocol level, complementing the
    hardware controller's operation. It manages SCLK generation with configurable 
    frequency/polarity, MOSI shifts based on TX data and timing, chip-select 
    management, and mode-specific edge timing (CPHA determines sample vs. drive edges).
    """
    
    def __init__(self, dut, config: SpiConfig):
        """Initialize SPI Master Driver."""
        self.dut = dut
        self.config = config
        self.log = dut._log
        
    async def transmit_byte(self, byte_val: int) -> int:
        """
        Transmit one SPI byte MSB-first and receive one byte simultaneously.
        
        Args:
            byte_val (int): 8-bit value to transmit (bit 7 sent first)
            
        Returns:
            int: 8-bit value received from MISO during transfer
        """
        tx_bits = [(byte_val >> (7 - i)) & 1 for i in range(8)]
        rx_byte = 0
        
        for bit_idx in range(8):
            if self.config.cpha == 0:
                await self._sclk_leading_edge()
                rx_bit = int(self.dut.miso_i.value)
                rx_byte = (rx_byte << 1) | rx_bit
                await self._sclk_trailing_edge()
            else:
                await self._sclk_leading_edge()
                await self._sclk_trailing_edge()
                rx_bit = int(self.dut.miso_i.value)
                rx_byte = (rx_byte << 1) | rx_bit
                
            if bit_idx < 7:
                self.dut.mosi_o.value = tx_bits[bit_idx + 1]
                
        return rx_byte
    
    async def _sclk_leading_edge(self):
        """Generate SCLK leading edge (idle to active transition)."""
        sclk_active = 1 - self.config.cpol
        for _ in range(self.config.bit_period_cycles):
            await RisingEdge(self.dut.clk_i)
            self.dut.sclk_o.value = sclk_active
    
    async def _sclk_trailing_edge(self):
        """Generate SCLK trailing edge (return to idle)."""
        sclk_idle = self.config.cpol
        for _ in range(self.config.bit_period_cycles):
            await RisingEdge(self.dut.clk_i)
            self.dut.sclk_o.value = sclk_idle


class SpiMonitor:
    """
    SPI Monitor - Passively observes SPI bus transactions.
    
    This monitor tracks SCLK edges, captures MOSI/MISO bit sequences, reconstructs
    byte-level transfers, times chip-select relative to SCLK, and emits transactions
    to a queue for scoreboard verification.
    """
    
    def __init__(self, dut, config: SpiConfig):
        """Initialize SPI Monitor."""
        self.dut = dut
        self.config = config
        self.log = dut._log
        self.transactions: List['SpiTransaction'] = []
        
    async def capture_transactions(self):
        """Continuously monitor SPI bus and capture transactions."""
        bit_count = 0
        mosi_bits = []
        miso_bits = []
        csn_currently_low = False
        prev_sclk = self.config.cpol
        
        while True:
            await RisingEdge(self.dut.clk_i)
            
            # Detect CSN assertion/deassertion
            csn_state = int(self.dut.csn_o.value) & (1 << self.config.csid)
            csn_low = (csn_state == 0)
            
            if csn_low and not csn_currently_low:
                self.log.debug(f"SPI: CS{self.config.csid} asserted")
                csn_currently_low = True
                bit_count = 0
                mosi_bits = []
                miso_bits = []
                
            elif not csn_low and csn_currently_low:
                if bit_count > 0:
                    mosi_val = self._bits_to_byte(mosi_bits)
                    miso_val = self._bits_to_byte(miso_bits)
                    self._emit_transaction(mosi_val, miso_val, bit_count)
                csn_currently_low = False
                bit_count = 0
                mosi_bits = []
                miso_bits = []
            
            sclk_current = int(self.dut.sclk_o.value)
            
            if csn_currently_low:
                is_leading_edge = (
                    (self.config.cpol == 0 and prev_sclk == 0 and sclk_current == 1) or
                    (self.config.cpol == 1 and prev_sclk == 1 and sclk_current == 0)
                )
                is_trailing_edge = (
                    (self.config.cpol == 0 and prev_sclk == 1 and sclk_current == 0) or
                    (self.config.cpol == 1 and prev_sclk == 0 and sclk_current == 1)
                )
                
                if self.config.cpha == 0 and is_leading_edge:
                    mosi_bits.append(int(self.dut.mosi_o.value))
                    miso_bits.append(int(self.dut.miso_i.value))
                    bit_count += 1
                elif self.config.cpha == 1 and is_trailing_edge:
                    mosi_bits.append(int(self.dut.mosi_o.value))
                    miso_bits.append(int(self.dut.miso_i.value))
                    bit_count += 1
                
                if bit_count == 8:
                    mosi_val = self._bits_to_byte(mosi_bits)
                    miso_val = self._bits_to_byte(miso_bits)
                    self._emit_transaction(mosi_val, miso_val, 8)
                    bit_count = 0
                    mosi_bits = []
                    miso_bits = []
            
            prev_sclk = sclk_current
    
    def _bits_to_byte(self, bits: List[int]) -> int:
        """Convert list of bits (MSB first) to byte value."""
        val = 0
        for bit in bits:
            val = (val << 1) | (bit & 1)
        return val
    
    def _emit_transaction(self, mosi_val: int, miso_val: int, bit_count: int):
        """Record one SPI transaction."""
        self.log.debug(f"SPI: TX 0x{mosi_val:02x}, RX 0x{miso_val:02x} ({bit_count} bits)")
        self.transactions.append(SpiTransaction(mosi_val, miso_val, bit_count))


@dataclass
class SpiTransaction:
    """Represents one SPI byte-level transaction."""
    mosi_byte: int
    miso_byte: int
    bit_count: int


class SpiProtocolAgent:
    """
    SPI Protocol Agent - Coordinates driver and monitor.
    
    This is the main interface for testbenches to interact with SPI protocol-level
    operations. Under normal operation, the hardware SPI controller generates SCLK
    and shifts data; this agent's monitor observes and records transactions.
    """
    
    def __init__(self, dut, config: Optional[SpiConfig] = None):
        """Initialize SPI protocol agent."""
        if config is None:
            config = SpiConfig()
        self.config = config
        self.driver = SpiMasterDriver(dut, config)
        self.monitor = SpiMonitor(dut, config)
        self.dut = dut
        self.log = dut._log
        
    async def start_monitor(self):
        """Start transaction monitor as background task."""
        cocotb.start_soon(self.monitor.capture_transactions())
        
    async def configure(self, **kwargs):
        """Update SPI configuration (CPOL, CPHA, clkdiv, timing parameters)."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.log.info(f"SPI configured: CPOL={self.config.cpol}, CPHA={self.config.cpha}, "
                     f"clkdiv=0x{self.config.clkdiv:04x}")
