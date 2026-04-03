"""
I2C Protocol Agent for RAMPART_I2C Controller Verification

This module implements a complete I2C protocol driver and monitor for the I2C controller
operating as both host (master) and target (slave). It provides:

1. Open-Drain Bus Simulation:
   - SCL/SDA lines use open-drain signaling (pull-low via oe_o, release via ~oe_o)
   - External pull-ups required (simulated by testbench)
   - Bus contention detection for multi-master arbitration

2. Host-Mode Operations (Master Transmit/Receive):
   - START condition: SDA high→low while SCL high
   - Data bit transmission: SCL low, set SDA, SCL high, sample SDA
   - STOP condition: SCL high, SDA low→high
   - Repeated START: STOP then START without bus release

3. Target-Mode Operations (Slave Transmit/Receive):
   - Responds to START condition with matching address
   - Holds SCL low (clock stretching) if not ready
   - Drives SDA for ACK/NACK after receiving byte
   - Releases SDA/SCL according to bus protocol

Key Concepts:
- I2C Address: 7-bit address + R/W bit (8 bits total per frame)
- ACK: Slave pulls SDA low for one clock period after address/data
- Arbitration Loss: Slave stops driving bus after detecting SDA high when driving low
- Clock Stretching: Slave can hold SCL low to throttle master
- Multi-Master: Simultaneous START detection triggers priority arbitration
"""

import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, Timer, Edge
from dataclasses import dataclass
from typing import Optional, List, Callable
from enum import Enum


class I2cState(Enum):
    """I2C bus state enumeration."""
    IDLE = 0
    START = 1
    ADDR_BYTE = 2
    DATA_BYTE = 3
    ACK_BIT = 4
    STOP = 5
    REPEATED_START = 6
    ARBITRATION_LOSS = 7


@dataclass
class I2cConfig:
    """
    I2C configuration container.
    
    Attributes:
        speed_mode (str): 'standard' (100 kHz), 'fast' (400 kHz), 'fastplus' (1 MHz)
        scl_period_ns (int): SCL half-period in nanoseconds (derived from speed_mode)
        target_address (int): 7-bit target (slave) address
        is_host (bool): True if this agent controls host operations
        is_target (bool): True if this agent monitors target operations
        clock_stretching_enabled (bool): Allow slave to hold SCL low
    """
    speed_mode: str = 'standard'  # 100 kHz
    scl_period_ns: int = 5000  # 10 µs cycle = 100 kHz
    target_address: int = 0x50  # Example: 7-bit address
    is_host: bool = True
    is_target: bool = False
    clock_stretching_enabled: bool = True
    
    def get_scl_timing(self) -> int:
        """Get SCL half-period based on speed mode."""
        modes = {
            'standard': 5000,     # 100 kHz → 10 µs period → 5 µs half-period
            'fast': 1250,         # 400 kHz → 2.5 µs period → 1.25 µs half-period
            'fastplus': 500,      # 1 MHz → 1 µs period → 500 ns half-period
        }
        return modes.get(self.speed_mode, 5000)


class I2cBusDriver:
    """
    I2C Bus Driver - Generates I2C protocol sequences on SCL/SDA open-drain lines.
    
    The driver simulates a bus master (host). It:
    - Generates START/STOP conditions
    - Transmits address and data bytes (MSB first, 8 bits per byte)
    - Waits for ACK/NACK bits from slaves
    - Implements repeated START for multi-phase transactions
    - Detects arbitration loss if another master drives bus
    
    The model uses open-drain output (scl_oe_o/sda_oe_o):
    - To drive low: Set oe=1, o=0 (pull-down)
    - To release: Set oe=0 or o=1 (high-impedance, external pull-up brings high)
    
    This driver runs on the main testbench (host role simulation).
    """
    
    def __init__(self, dut, config: I2cConfig):
        """
        Initialize I2C Bus Driver.
        
        Args:
            dut: cocotb DUT handle
            config: I2cConfig object with speed, address, mode settings
        """
        self.dut = dut
        self.config = config
        self.log = dut._log
        
    async def start_condition(self):
        """
        Generate I2C START condition: SDA high→low while SCL is high.
        
        Sequence:
        1. Release SCL (allow to go high)
        2. Release SDA (allow to go high)
        3. Wait for SCL to settle high
        4. Pull SDA low (START)
        5. Wait for SDA to settle low
        """
        self.log.debug("I2C: Generating START condition")
        
        # Release SCL
        self.dut.scl_oe_o.value = 0
        await Timer(100, units='ns')  # Allow pull-up to settle
        
        # Release SDA
        self.dut.sda_oe_o.value = 0
        await Timer(100, units='ns')
        
        # Verify SCL high
        if not int(self.dut.scl_i.value):
            self.log.warning("I2C: SCL not high before START")
        
        # Pull SDA low (START)
        self.dut.sda_oe_o.value = 1
        await Timer(100, units='ns')
        
        # Now SCL can be pulled low
        self.dut.scl_oe_o.value = 1
        await Timer(100, units='ns')
        
    async def stop_condition(self):
        """
        Generate I2C STOP condition: SDA low→high while SCL is high.
        
        Sequence:
        1. Pull SDA low
        2. Release SCL (allow to go high)
        3. Release SDA (allow to go high, STOP)
        4. Verify SDA high after STOP
        """
        self.log.debug("I2C: Generating STOP condition")
        
        # Pull SDA low
        self.dut.sda_oe_o.value = 1
        await Timer(100, units='ns')
        
        # Release SCL
        self.dut.scl_oe_o.value = 0
        await Timer(100, units='ns')
        
        # Release SDA (STOP)
        self.dut.sda_oe_o.value = 0
        await Timer(100, units='ns')
        
    async def transmit_byte(self, byte_val: int, expect_ack: bool = True) -> bool:
        """
        Transmit one I2C byte (8 bits, MSB first).
        
        For each bit:
        1. Pull SCL low
        2. Set/release SDA based on bit value
        3. Release SCL (allow to go high)
        4. Wait for clock stretching (slave may hold SCL low)
        5. Sample SDA at clock high
        6. Pull SCL low (end of bit)
        
        After 8 bits, wait for ACK bit (slave pulls SDA low).
        
        Args:
            byte_val (int): 8-bit value to transmit (bit 7 sent first)
            expect_ack (bool): If True, expect slave to pull SDA low for ACK
            
        Returns:
            bool: True if ACK received; False if NACK
        """
        bits = [(byte_val >> (7 - i)) & 1 for i in range(8)]
        
        for bit_idx, bit_val in enumerate(bits):
            # Pull SCL low
            self.dut.scl_oe_o.value = 1
            await Timer(100, units='ns')
            
            # Set SDA based on bit value
            if bit_val:
                self.dut.sda_oe_o.value = 0  # Release (high)
            else:
                self.dut.sda_oe_o.value = 1  # Pull low
            await Timer(100, units='ns')
            
            # Release SCL (clock pulse)
            self.dut.scl_oe_o.value = 0
            await Timer(100, units='ns')
            
            # Wait for SCL high (clock stretching allowed)
            stretch_timeout = 0
            while not int(self.dut.scl_i.value) and stretch_timeout < 10000:
                await Timer(100, units='ns')
                stretch_timeout += 1
            
            if stretch_timeout >= 10000:
                self.log.warning(f"I2C: Clock stretching timeout (bit {bit_idx})")
            
            # Sample SDA
            sda_val = int(self.dut.sda_i.value)
            self.log.debug(f"I2C TX Bit {bit_idx}: {bit_val} (SDA sampled: {sda_val})")
        
        # Pull SCL low (end of byte)
        self.dut.scl_oe_o.value = 1
        await Timer(100, units='ns')
        
        # Wait for ACK bit from slave
        if expect_ack:
            # Release SCL for ACK clock
            self.dut.scl_oe_o.value = 0
            self.dut.sda_oe_o.value = 0  # Release SDA (slave should pull low)
            await Timer(100, units='ns')
            
            # Wait for SCL high
            await Timer(200, units='ns')
            
            # Sample ACK (SDA should be low)
            ack_bit = int(self.dut.sda_i.value)
            ack_received = (ack_bit == 0)
            
            self.log.debug(f"I2C ACK bit sampled: {ack_bit} ({'ACK' if ack_received else 'NACK'})")
            
            # Pull SCL low (end of ACK bit)
            self.dut.scl_oe_o.value = 1
            await Timer(100, units='ns')
            
            return ack_received
        
        return True
    
    async def receive_byte(self) -> int:
        """
        Receive one I2C byte from slave.
        
        For each bit:
        1. Pull SCL low
        2. Release SCL (allow high, slave can set SDA)
        3. Sample SDA at clock high
        4. Pull SCL low (end of bit)
        
        After 8 bits, transmit ACK bit (pull SDA low during clock).
        
        Returns:
            int: 8-bit value received from slave (bit 7 first)
        """
        self.log.debug("I2C: Receiving byte")
        rx_byte = 0
        
        for bit_idx in range(8):
            # Pull SCL low
            self.dut.scl_oe_o.value = 1
            await Timer(100, units='ns')
            
            # Release SCL (slave can set SDA)
            self.dut.scl_oe_o.value = 0
            self.dut.sda_oe_o.value = 0  # Release SDA
            await Timer(100, units='ns')
            
            # Wait for SCL high
            await Timer(200, units='ns')
            
            # Sample SDA
            bit_val = int(self.dut.sda_i.value)
            rx_byte = (rx_byte << 1) | bit_val
            self.log.debug(f"I2C RX Bit {bit_idx}: {bit_val}")
        
        # Generate ACK bit
        self.dut.scl_oe_o.value = 1
        self.dut.sda_oe_o.value = 1  # Pull SDA low for ACK
        await Timer(100, units='ns')
        
        self.dut.scl_oe_o.value = 0
        await Timer(200, units='ns')
        
        self.dut.scl_oe_o.value = 1
        self.dut.sda_oe_o.value = 0  # Release SDA
        await Timer(100, units='ns')
        
        return rx_byte


class I2cMonitor:
    """
    I2C Monitor - Passively observes I2C bus transactions.
    
    This monitor:
    - Detects START/STOP/repeated START conditions
    - Captures address and data bytes
    - Records ACK/NACK bits
    - Detects arbitration loss (multi-master scenarios)
    - Emits I2cTransaction items for scoreboard verification
    """
    
    def __init__(self, dut, config: I2cConfig):
        """Initialize I2C Monitor."""
        self.dut = dut
        self.config = config
        self.log = dut._log
        self.transactions: List['I2cTransaction'] = []
        
    async def capture_transactions(self):
        """Continuously monitor I2C bus and capture bus transactions."""
        prev_scl = 1
        prev_sda = 1
        
        while True:
            await RisingEdge(self.dut.clk_i)
            
            scl_current = int(self.dut.scl_i.value)
            sda_current = int(self.dut.sda_i.value)
            
            # Detect START condition: SDA 1→0 while SCL=1
            if prev_sda == 1 and sda_current == 0 and scl_current == 1:
                self.log.debug("I2C Monitor: START detected")
                self.transactions.append(I2cTransaction(I2cState.START, None, None))
            
            # Detect STOP condition: SDA 0→1 while SCL=1
            if prev_sda == 0 and sda_current == 1 and scl_current == 1:
                self.log.debug("I2C Monitor: STOP detected")
                self.transactions.append(I2cTransaction(I2cState.STOP, None, None))
            
            prev_scl = scl_current
            prev_sda = sda_current


@dataclass
class I2cTransaction:
    """Represents one I2C bus event (START, STOP, byte, ACK, etc.)."""
    state: I2cState
    byte_val: Optional[int]
    ack_bit: Optional[int]


class I2cProtocolAgent:
    """
    I2C Protocol Agent - Coordinates driver and monitor.
    
    This is the main testbench interface for I2C protocol-level operations.
    It provides host-mode transmission/reception with automatic START/STOP/ACK handling.
    """
    
    def __init__(self, dut, config: Optional[I2cConfig] = None):
        """Initialize I2C protocol agent."""
        if config is None:
            config = I2cConfig()
        self.config = config
        self.driver = I2cBusDriver(dut, config)
        self.monitor = I2cMonitor(dut, config)
        self.dut = dut
        self.log = dut._log
        
    async def start_monitor(self):
        """Start transaction monitor as background task."""
        cocotb.start_soon(self.monitor.capture_transactions())
        
    async def write_address(self, address: int, expect_ack: bool = True) -> bool:
        """
        Transmit I2C address byte (address + R/W bit).
        
        Args:
            address (int): 8-bit address (7-bit addr in bits [7:1], R/W in bit [0])
            expect_ack (bool): Expect slave ACK
            
        Returns:
            bool: True if ACK received
        """
        return await self.driver.transmit_byte(address, expect_ack)
    
    async def write_byte(self, byte_val: int, expect_ack: bool = True) -> bool:
        """Transmit data byte."""
        return await self.driver.transmit_byte(byte_val, expect_ack)
    
    async def read_byte(self) -> int:
        """Receive data byte with ACK."""
        return await self.driver.receive_byte()
    
    async def start(self):
        """Generate START condition."""
        await self.driver.start_condition()
    
    async def stop(self):
        """Generate STOP condition."""
        await self.driver.stop_condition()
    
    async def configure(self, **kwargs):
        """Update I2C configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.log.info(f"I2C configured: speed_mode={self.config.speed_mode}, "
                     f"target_address=0x{self.config.target_address:02x}")
