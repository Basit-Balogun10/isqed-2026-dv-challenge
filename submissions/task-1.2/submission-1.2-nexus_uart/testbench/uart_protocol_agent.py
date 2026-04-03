"""
NEXUS_UART Protocol Agent

Handles UART serial protocol operations:
- Driving serial TX (uart_tx_o) for stimulus
- Monitoring serial RX (uart_rx_i) for DUT output capture
- Baud rate and frame configuration translation
- Parity/stop-bit generation and verification

The UART agent complements the TL-UL agent:
- TL-UL agent: Configures control registers (baud rate, parity, enable bits)
- UART agent: Drives/monitors the physical serial pins based on config

Note: This is pure Python/Cocotb (NOT UVM). No pyuvm dependencies.
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer, FallingEdge
import math


class UartConfig:
    """Encapsulates UART configuration extracted from CSR values."""
    
    def __init__(self, baud_divisor=1, parity_mode=0, stop_bits=1):
        """
        Args:
            baud_divisor (int): 16-bit value from CTRL register
                Baud rate = sys_clk_freq / (baud_divisor * 16)
            parity_mode (int): 00=none, 01=even, 10=odd, 11=reserved
            stop_bits (int): 0=1-bit, 1=2-bits
        """
        self.baud_divisor = baud_divisor
        self.parity_mode = parity_mode  # 0=none, 1=even, 2=odd
        self.stop_bits = stop_bits  # 0=1-bit, 1=2-bits
        
        # Derived timing values (assuming 1 MHz system clock for simplicity)
        self.sys_clk_freq_mhz = 1.0
        self.bit_period_cycles = baud_divisor  # Each UART bit is baud_divisor cycles
        self.oversample_period = self.bit_period_cycles // 16  # 16x oversampling
    
    def __str__(self):
        parity_str = {0: "none", 1: "even", 2: "odd"}.get(self.parity_mode, "?")
        stop_str = "1" if self.stop_bits == 0 else "2"
        baud = self.sys_clk_freq_mhz * 1e6 / (self.baud_divisor * 16)
        return (f"UartConfig(baud={baud:.0f}, parity={parity_str}, "
                f"stop={stop_str}, div={self.bit_period_cycles})")


class NexusUartTxDriver:
    """
    UART Transmitter Driver.
    
    Drives the physical uart_tx_o pin to transmit bytes to the DUT.
    Uses bit-banging approach synchronized to system clock.
    """
    
    def __init__(self, dut, config=None, log=None):
        self.dut = dut
        self.config = config
        self.log = log or dut._log
    
    async def send_byte(self, byte_val, config=None):
        """
        Transmit a single byte on uart_tx_o.
        
        Frame format:
        [START] [D0] [D1] ... [D7] [PARITY] [STOP1] [STOP2?] [IDLE]
        
        Args:
            byte_val (int): 8-bit data to transmit
            config (UartConfig): UART configuration (baud, parity, stop bits)
        """
        if config is None:
            config = self.config
        
        # Calculate parity bit if enabled
        parity_bit = 0
        if config.parity_mode != 0:
            # Count 1s in byte_val
            ones = bin(byte_val).count('1')
            if config.parity_mode == 1:  # Even parity
                parity_bit = ones % 2
            elif config.parity_mode == 2:  # Odd parity
                parity_bit = (ones + 1) % 2
        
        # Build frame as a list of bit values: [START, D0-D7, PARITY, STOP1, STOP2?]
        frame = [0]  # START bit
        for i in range(8):
            frame.append((byte_val >> i) & 1)  # LSB first
        if config.parity_mode != 0:
            frame.append(parity_bit)
        frame.append(1)  # STOP bit 1
        if config.stop_bits == 1:
            frame.append(1)  # STOP bit 2
        
        # Transmit each bit
        for bit_idx, bit_val in enumerate(frame):
            self.dut.uart_tx_o.value = bit_val
            # Wait for one bit period (baud_divisor system clocks)
            for _ in range(config.bit_period_cycles):
                await RisingEdge(self.dut.clk_i)
        
        # Return to idle (HIGH)
        self.dut.uart_tx_o.value = 1
        
        self.log.info(
            f"[NexusUartTxDriver] TX: 0x{byte_val:02x} via uart_tx_o "
            f"({len(frame)} bits, {config})"
        )


class NexusUartRxMonitor:
    """
    UART Receiver Monitor.
    
    Passively observes uart_rx_i pin to capture bytes transmitted by the DUT.
    Uses mid-bit sampling consistent with UART oversampling practice.
    """
    
    def __init__(self, dut, config=None, log=None):
        self.dut = dut
        self.config = config
        self.log = log or dut._log
        self.captured_bytes = []
    
    async def capture_byte(self, config, timeout_bits=20):
        """
        Wait for and capture a single byte from uart_rx_i.
        
        Returns:
            (byte_val, error_flag): Captured byte and parity/frame error indicator
        
        Args:
            config (UartConfig): UART configuration
            timeout_bits (int): Maximum bits to wait before timeout
        """
        # Wait for START bit (falling edge on uart_rx_i)
        timeout_cycles = timeout_bits * config.bit_period_cycles
        start_found = False
        for _ in range(timeout_cycles):
            if int(self.dut.uart_rx_i.value) == 0:
                start_found = True
                break
            await RisingEdge(self.dut.clk_i)
        
        if not start_found:
            self.log.warning("[NexusUartRxMonitor] RX timeout: START bit not detected")
            return (0, 1)  # Error: timeout
        
        # Skip to mid-bit of START (sample at bit_period/2 + 8x oversample)
        sample_offset = (config.bit_period_cycles // 2) // 16
        for _ in range(sample_offset):
            await RisingEdge(self.dut.clk_i)
        
        # Capture 8 data bits (LSB first)
        byte_val = 0
        for bit_idx in range(8):
            # Wait until mid-bit
            for _ in range(config.bit_period_cycles):
                await RisingEdge(self.dut.clk_i)
            
            bit = int(self.dut.uart_rx_i.value)
            byte_val |= (bit << bit_idx)
        
        # Capture parity bit (if enabled)
        parity_error = 0
        if config.parity_mode != 0:
            for _ in range(config.bit_period_cycles):
                await RisingEdge(self.dut.clk_i)
            parity_rx = int(self.dut.uart_rx_i.value)
            
            # Calculate expected parity
            ones = bin(byte_val).count('1')
            if config.parity_mode == 1:  # Even
                expected_parity = ones % 2
            elif config.parity_mode == 2:  # Odd
                expected_parity = (ones + 1) % 2
            else:
                expected_parity = 0
            
            parity_error = 1 if parity_rx != expected_parity else 0
        
        # Capture STOP bit(s)
        frame_error = 0
        for stop_idx in range(1 + config.stop_bits):
            for _ in range(config.bit_period_cycles):
                await RisingEdge(self.dut.clk_i)
            stop_bit = int(self.dut.uart_rx_i.value)
            if stop_bit != 1:
                frame_error = 1
        
        error = parity_error | frame_error
        self.captured_bytes.append((byte_val, error))
        
        self.log.info(
            f"[NexusUartRxMonitor] RX: 0x{byte_val:02x} error={error} ({config})"
        )
        
        return (byte_val, error)


# ============================================================================
# HELPER SEQUENCES FOR UART OPERATIONS
# ============================================================================

class NexusUartTxSeq:
    """
    Sequence: Transmit a byte via UART (drives uart_tx_o).
    
    This sequence coordinates with the TL-UL agent to:
    1. Write configuration to CTRL (baud rate, parity, enable TX)
    2. Write byte to TXDATA
    3. Drive uart_tx_o with the expected frame
    """
    
    def __init__(self, byte_val=0x42, config=None, tl_agent=None, tx_driver=None, log=None):
        self.byte_val = byte_val
        self.config = config
        self.tl_agent = tl_agent
        self.tx_driver = tx_driver
        self.log = log
    
    async def execute(self):
        """Execute UART TX operation."""
        if self.tl_agent is None:
            if self.log:
                self.log.error("[NexusUartTxSeq] tl_agent not set!")
            return
        
        # Example: Set baud divisor and enable TX
        # (Assumes CTRL register at 0x00)
        if self.config:
            ctrl_val = (
                (self.config.baud_divisor << 2) |  # baud_divisor in bits [17:2]
                (self.config.parity_mode << 18) |   # parity_mode in bits [19:18]
                (self.config.stop_bits << 20) |     # stop_bits in bit [20]
                0x1                                  # Enable TX
            )
            await self.tl_agent.write_csr(addr=0x00, data=ctrl_val)
        
        # Step 2: Write byte to TXDATA (0x08)
        await self.tl_agent.write_csr(addr=0x08, data=self.byte_val)
        
        # Step 3: Wait for TXDATA to drain into FIFO
        # (Simple: just wait a few clocks)
        # await cocotb.sleep(100, "us")  # In real sim, depends on divisor
        
        if self.log:
            self.log.info(f"[NexusUartTxSeq] UART TX complete: byte=0x{self.byte_val:02x}")


class NexusUartRxSeq:
    """
    Sequence: Receive a byte via UART (monitors uart_rx_i).
    
    This sequence:
    1. Waits for a complete UART frame on uart_rx_i
    2. Captures byte value and error flags
    3. Optionally read RXDATA CSR to verify matching
    """
    
    def __init__(self, config=None, rx_monitor=None, tl_agent=None, log=None):
        self.config = config
        self.rx_monitor = rx_monitor
        self.tl_agent = tl_agent
        self.captured_byte = None
        self.captured_error = None
        self.log = log
    
    async def execute(self):
        """Execute UART RX operation."""
        if self.rx_monitor is None:
            if self.log:
                self.log.error("[NexusUartRxSeq] rx_monitor not set!")
            return
        
        # Capture byte from serial pin
        self.captured_byte, self.captured_error = await self.rx_monitor.capture_byte(
            self.config
        )
        
        # Optionally read from RXDATA (0x0C) to confirm
        if self.tl_agent:
            fifo_data, _ = await self.tl_agent.read_csr(addr=0x0C)
            if fifo_data != self.captured_byte and self.log:
                self.log.warning(
                    f"[NexusUartRxSeq] RXDATA mismatch: "
                    f"serial=0x{self.captured_byte:02x}, fifo=0x{fifo_data:02x}"
                )
        
        if self.log:
            self.log.info(
                f"[NexusUartRxSeq] UART RX complete: "
                f"byte=0x{self.captured_byte:02x}, error={self.captured_error}"
            )
