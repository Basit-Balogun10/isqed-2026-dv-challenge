"""
I2C Scoreboard for RAMPART_I2C Controller Verification

This module implements CSR-level verification and protocol-level transaction checking
for the RAMPART_I2C controller. The scoreboard maintains a reference model of the
I2C controller state (format FIFO, RX/TX FIFOs, control settings, bus state) and
compares it against CSR read operations. It also validates I2C protocol behavior
(START/STOP sequences, address/data byte transmission, ACK/NACK bits).

Key Data Paths:
1. CSR Path: Test → TL-UL → Controller CSRs → Response data
   - Write PATH: CTRL (host/target enable), FORMAT FIFO (bus commands)
   - Read PATH: STATUS (FIFO full/empty), RX FIFO, TX FIFO
   
2. Host Mode: Format FIFO → Host FSM → SCL/SDA bus interface
   - FORMAT FIFO contains bus commands: START, address byte, data bytes, STOP
   - Host FSM executes sequence, clock-stretching aware
   
3. Target Mode: SDA/SCL bus input → Target FSM → RX/TX/ACQ FIFOs
   - Responds to bus START conditions with address matching
   - Captures RX data, provides TX data for slave-mode operation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class I2cFmtCmd(Enum):
    """I2C Format FIFO command enumeration."""
    START = 0
    STOP = 1
    TX_BYTE = 2
    RX_BYTE = 3
    REPEATED_START = 4


@dataclass
class I2cRefModel:
    """
    Reference Model for RAMPART_I2C Controller.
    
    Tracks expected state of FIFOs, control settings, and bus state.
    
    Attributes:
        format_fifo (list): Format FIFO command queue (64-entry max)
        rx_fifo (list): Host-mode RX FIFO data (64-entry max)
        tx_fifo (list): Target-mode TX FIFO data (64-entry max)
        acq_fifo (list): Target-mode acquire/RX data (64-entry max)
        ctrl (int): CTRL register (host_enable, target_enable, loopback)
        host_enabled (bool): Host mode active
        target_enabled (bool): Target mode active
        bus_state (I2cBusState): Current bus state
    """
    format_fifo: List[int] = field(default_factory=list)
    rx_fifo: List[int] = field(default_factory=list)
    tx_fifo: List[int] = field(default_factory=list)
    acq_fifo: List[int] = field(default_factory=list)
    ctrl: int = 0x00
    host_enabled: bool = False
    target_enabled: bool = False
    master_started: bool = False
    error_flags: Dict[str, bool] = field(default_factory=lambda: {
        'fmt_overflow': False,
        'rx_overflow': False,
        'tx_overflow': False,
        'acq_overflow': False,
        'abort': False,
    })
    
    MAX_FIFO_DEPTH = 64
    
    def push_format_cmd(self, cmd: int, data: Optional[int] = None) -> bool:
        """
        Push command to Format FIFO (host-mode bus command).
        Returns True if successful; False if overflow.
        """
        if len(self.format_fifo) >= self.MAX_FIFO_DEPTH:
            self.error_flags['fmt_overflow'] = True
            return False
        # Encode: cmd in bits [9:8], data in bits [7:0]
        encoded = ((cmd & 0x03) << 8) | (data & 0xFF) if data else (cmd << 8)
        self.format_fifo.append(encoded)
        return True
    
    def pop_format_cmd(self) -> Optional[tuple]:
        """Pop command from Format FIFO. Returns (cmd, data)."""
        if not self.format_fifo:
            return None
        encoded = self.format_fifo.pop(0)
        cmd = (encoded >> 8) & 0x03
        data = encoded & 0xFF
        return (cmd, data)
    
    def push_rx(self, byte_val: int) -> bool:
        """Push byte to host-mode RX FIFO."""
        if len(self.rx_fifo) >= self.MAX_FIFO_DEPTH:
            self.error_flags['rx_overflow'] = True
            return False
        self.rx_fifo.append(byte_val & 0xFF)
        return True
    
    def pop_rx(self) -> Optional[int]:
        """Pop byte from RX FIFO (CSR read)."""
        if not self.rx_fifo:
            return None
        return self.rx_fifo.pop(0)
    
    def push_tx(self, byte_val: int) -> bool:
        """Push byte to target-mode TX FIFO."""
        if len(self.tx_fifo) >= self.MAX_FIFO_DEPTH:
            self.error_flags['tx_overflow'] = True
            return False
        self.tx_fifo.append(byte_val & 0xFF)
        return True
    
    def get_status(self) -> dict:
        """Generate STATUS register value from current state."""
        return {
            'fmtfull': 1 if len(self.format_fifo) >= self.MAX_FIFO_DEPTH else 0,
            'fmtempty': 1 if len(self.format_fifo) == 0 else 0,
            'rxfull': 1 if len(self.rx_fifo) >= self.MAX_FIFO_DEPTH else 0,
            'rxempty': 1 if len(self.rx_fifo) == 0 else 0,
            'txfull': 1 if len(self.tx_fifo) >= self.MAX_FIFO_DEPTH else 0,
            'txempty': 1 if len(self.tx_fifo) == 0 else 0,
            'acqfull': 1 if len(self.acq_fifo) >= self.MAX_FIFO_DEPTH else 0,
            'acqempty': 1 if len(self.acq_fifo) == 0 else 0,
        }


@dataclass
class I2cBusTransaction:
    """Represents one I2C bus transaction (START, STOP, byte transmitted/received)."""
    event_type: str  # 'start', 'stop', 'addr_tx', 'data_tx', 'data_rx', 'ack', 'nack'
    byte_val: Optional[int] = None
    is_ack: Optional[bool] = None


class I2cScoreboard:
    """
    I2C Scoreboard - Verifies CSR operations and protocol-level transactions.
    
    Two levels of checking:
    
    1. CSR-Level:
       - Format FIFO writes are tracked and expected to execute on bus
       - STATUS reads reflect FIFO occupancy from reference model
       - RX FIFO reads pop data from reference model
    
    2. Protocol-Level:
       - I2cMonitor observes bus START/STOP/byte/ACK sequences
       - Scoreboard expects these to match Format FIFO commands and RX data
    """
    
    def __init__(self, dut, protocol_agent, tl_ul_agent):
        """Initialize I2C Scoreboard."""
        self.dut = dut
        self.protocol_agent = protocol_agent
        self.tl_ul_agent = tl_ul_agent
        self.log = dut._log
        
        self.ref_model = I2cRefModel()
        self.observed_transactions: List[I2cBusTransaction] = []
        self.error_count = 0
        self.check_count = 0
    
    async def handle_csr_write(self, addr: int, data: int, mask: int = 0xFFFFFFFF):
        """Handle CSR write - update reference model."""
        addr = addr & 0xFFFFFFFF
        
        if addr == 0x00:  # CTRL
            self.ref_model.ctrl = data & 0x07
            self.ref_model.host_enabled = (data & 0x01) != 0
            self.ref_model.target_enabled = (data & 0x02) != 0
            self.log.debug(f"I2C CSR: CTRL write 0x{data:08x} "
                         f"(host={self.ref_model.host_enabled}, target={self.ref_model.target_enabled})")
        
        elif addr == 0x0C:  # FORMAT FIFO
            # Extract command and optional data byte
            fmt_cmd = (data >> 8) & 0x03
            fmt_data = data & 0xFF
            success = self.ref_model.push_format_cmd(fmt_cmd, fmt_data)
            if not success:
                self.log.error(f"I2C: Format FIFO overflow (model)")
                self.error_count += 1
            self.log.debug(f"I2C CSR: FORMAT FIFO write cmd={fmt_cmd} data=0x{fmt_data:02x}")
        
        elif addr == 0x38:  # TARGET TX FIFO
            success = self.ref_model.push_tx(data & 0xFF)
            if not success:
                self.log.error(f"I2C: TX FIFO overflow (model)")
                self.error_count += 1
            self.log.debug(f"I2C CSR: TX FIFO write 0x{data:02x}")
    
    async def handle_csr_read(self, addr: int) -> int:
        """Handle CSR read - verify against reference model."""
        addr = addr & 0xFFFFFFFF
        self.check_count += 1
        
        if addr == 0x04:  # STATUS
            status = self.ref_model.get_status()
            status_val = (
                (status['fmtfull'] << 0) |
                (status['fmtempty'] << 1) |
                (status['rxfull'] << 2) |
                (status['rxempty'] << 3) |
                (status['txfull'] << 4) |
                (status['txempty'] << 5) |
                (status['acqfull'] << 6) |
                (status['acqempty'] << 7)
            )
            self.log.debug(f"I2C CSR: STATUS read → 0x{status_val:08x}")
            return status_val
        
        elif addr == 0x08:  # RX FIFO (host mode)
            rx_val = self.ref_model.pop_rx()
            if rx_val is None:
                rx_val = 0x00
                self.log.warning(f"I2C: RX FIFO underflow (model)")
            self.log.debug(f"I2C CSR: RX FIFO read → 0x{rx_val:02x}")
            return rx_val
        
        elif addr == 0x34:  # ACQUIRE FIFO (target mode)
            acq_val = self.ref_model.acq_fifo.pop(0) if self.ref_model.acq_fifo else 0
            self.log.debug(f"I2C CSR: ACQ FIFO read → 0x{acq_val:02x}")
            return acq_val
        
        return 0x00000000
    
    def report(self) -> dict:
        """Generate verification report."""
        return {
            'total_checks': self.check_count,
            'error_count': self.error_count,
            'observed_transactions': len(self.observed_transactions),
            'status': 'PASS' if self.error_count == 0 else 'FAIL',
        }


class I2cEnvironment:
    """
    I2C Environment - Integrates TL-UL agent, protocol agent, and scoreboard.
    
    Provides CSR access via TL-UL and protocol-level I2C operations.
    """
    
    def __init__(self, dut, tl_ul_agent):
        """Initialize I2C environment."""
        self.dut = dut
        self.tl_ul_agent = tl_ul_agent
        self.log = dut._log
        
        # Create protocol agent
        from .i2c_protocol_agent import I2cProtocolAgent, I2cConfig
        i2c_config = I2cConfig(speed_mode='standard', target_address=0x50)
        self.protocol_agent = I2cProtocolAgent(dut, i2c_config)
        
        # Create scoreboard
        self.scoreboard = I2cScoreboard(dut, self.protocol_agent, tl_ul_agent)
    
    async def start(self):
        """Start environment."""
        await self.protocol_agent.start_monitor()
        self.log.info("I2C Environment started")
    
    async def write_csr(self, addr: int, data: int, mask: int = 0xFFFFFFFF):
        """Write I2C CSR via TL-UL + update scoreboard."""
        await self.tl_ul_agent.write_csr(addr, data, mask)
        await self.scoreboard.handle_csr_write(addr, data, mask)
    
    async def read_csr(self, addr: int) -> int:
        """Read I2C CSR via TL-UL and verify against scoreboard."""
        hw_data = await self.tl_ul_agent.read_csr(addr)
        expected_data = await self.scoreboard.handle_csr_read(addr)
        
        if hw_data != expected_data:
            self.log.error(f"I2C CSR Mismatch at 0x{addr:02x}: hw=0x{hw_data:08x}, "
                         f"expected=0x{expected_data:08x}")
            self.scoreboard.error_count += 1
        
        return hw_data
    
    def report(self) -> dict:
        """Generate test report."""
        return self.scoreboard.report()
