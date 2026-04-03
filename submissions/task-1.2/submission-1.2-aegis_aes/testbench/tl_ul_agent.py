"""
TileLink-UL Agent

Integrates driver, monitor, and helper methods for CSR transactions.
This is the main interface that tests use to interact with the TL-UL bus.

Philosophy:
- Pure Python class (not UVM agent)
- Coordinates TlUlDriver and TlUlMonitor
- Provides high-level CSR helpers (write_csr, read_csr)
- Runs monitor as background cocotb task
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from .tl_ul_driver import TlUlDriver
from .tl_ul_monitor import TlUlMonitor
from .tl_ul_sequences import write_sequence, read_sequence, burst_sequence, random_sequence


class TlUlAgent:
    """
    TileLink-UL Bus Agent.
    
    Main interface for CSR transactions. Provides:
    - Low-level: driver.drive_seq_item(item)
    - Medium-level: await agent.write_csr(addr, data), await agent.read_csr(addr)
    - High-level: Use sequence helpers (write_sequence, read_sequence, etc.)
    
    Monitor runs in background, capturing all transactions and broadcasting
    to registered callbacks (useful for scoreboarding).
    
    Example Usage in Test:
        @cocotb.test
        async def test_csr_io(dut):
            agent = TlUlAgent(dut, log=dut._log)
            
            # Start monitor (runs in background)
            monitor_task = await cocotb.start(agent.monitor.run())
            
            # Simple write
            await agent.write_csr(addr=0x08, data=0xDEADBEEF)
            
            # Simple read
            data, error = await agent.read_csr(addr=0x04)
            print(f"Read: 0x{data:08x}, error={error}")
            
            # Burst operations
            responses = await burst_sequence(
                agent.driver,
                [0x00, 0x04, 0x08],
                [0,    4,    0   ],
                [0x11, 0,    0x22]
            )
    """
    
    def __init__(self, dut, log=None):
        """
        Initialize TL-UL agent.
        
        Args:
            dut: Cocotb DUT handle
            log: Optional logger (uses dut._log by default)
        """
        self.dut = dut
        self.log = log or dut._log
        
        # Initialize sub-components
        self.driver = TlUlDriver(dut, log=self.log)
        self.monitor = TlUlMonitor(dut, log=self.log)
        
        self.log.info("[TlUlAgent] Initialized TL-UL agent for DUT")
    
    async def start_monitor(self):
        """
        Start the monitor as a background task.
        
        Call this once at the beginning of your test.
        Monitor runs continuously, capturing all bus transactions.
        
        Returns:
            cocotb task handle (can be used with cocotb.kill() if needed)
            
        Example:
            monitor_task = await agent.start_monitor()
            # ... test code ...
            await cocotb.kill(monitor_task)
        """
        self.log.info("[TlUlAgent] Starting monitor background task")
        return await cocotb.start(self.monitor.run())
    
    def register_monitor_callback(self, callback_func):
        """
        Register a function to be called for each monitored transaction.
        
        Callback receives TlUlSeqItem with complete transaction data.
        Useful for scoreboards, coverage collection, etc.
        
        Args:
            callback_func: Function(TlUlSeqItem) or async coroutine
            
        Example (in scoreboard):
            def scoreboard_callback(item):
                assert item.response_error == 0, f"Unexpected error on {item.address:08x}"
            
            agent.register_monitor_callback(scoreboard_callback)
        """
        self.monitor.register_callback(callback_func)
    
    # ========================================================================
    # CSR Helper Methods
    # ========================================================================
    
    async def write_csr(self, addr, data, mask=0xF):
        """
        Perform a single CSR write via TL-UL.
        
        Args:
            addr (int): 32-bit byte address
            data (int): 32-bit write data
            mask (int): 4-bit byte enable mask (default 0xF = full write)
            
        Returns:
            response_error (int): 0 if success, 1 if device error
            
        Example:
            await agent.write_csr(0x08, 0x12345678)
        """
        return await write_sequence(self.driver, addr, data, mask)
    
    async def read_csr(self, addr):
        """
        Perform a single CSR read via TL-UL.
        
        Args:
            addr (int): 32-bit byte address
            
        Returns:
            (data, error) tuple: 32-bit read data and error flag
            
        Example:
            data, error = await agent.read_csr(0x04)
            if error:
                self.log.error(f"Read error at address 0x{addr:08x}")
        """
        return await read_sequence(self.driver, addr)
    
    async def write_csr_masked(self, addr, data, mask):
        """
        Perform a masked CSR write (partial update).
        
        Useful for writing only certain bits without affecting others.
        
        Args:
            addr (int): 32-bit byte address
            data (int): Write data (only bits set in mask are written)
            mask (int): 4-bit byte enable mask
            
        Example:
            # Write lower byte only (assume upper 3 bytes unchanged)
            await agent.write_csr_masked(0x00, 0xFF, mask=0x1)
        """
        return await write_sequence(self.driver, addr, data, mask)
    
    async def read_and_compare(self, addr, expected_data, mask=0xF):
        """
        Read CSR and compare against expected value.
        
        Args:
            addr (int): Target address
            expected_data (int): Expected read data
            mask (int): Mask for comparison (only compare bits set in mask)
            
        Returns:
            bool: True if match, False otherwise
            
        Example:
            if await agent.read_and_compare(0x04, 0x12345678, mask=0xF):
                print("CSR value matches!")
        """
        data, error = await self.read_csr(addr)
        
        if error:
            self.log.error(f"[ReadCompare] Read error at 0x{addr:08x}")
            return False
        
        if (data & mask) != (expected_data & mask):
            self.log.error(
                f"[ReadCompare] Mismatch at 0x{addr:08x}: "
                f"got 0x{data:08x}, expected 0x{expected_data:08x} (mask 0x{mask:x})"
            )
            return False
        
        self.log.info(
            f"[ReadCompare] Match at 0x{addr:08x}: "
            f"0x{data:08x} (mask 0x{mask:x})"
        )
        return True
    
    async def burst_read(self, start_addr, num_reads):
        """
        Perform a burst of consecutive read operations.
        
        Args:
            start_addr (int): Starting address (must be 4-byte aligned)
            num_reads (int): Number of consecutive 32-bit reads
            
        Returns:
            data_list: List of (data, error) tuples
            
        Example:
            data_list = await agent.burst_read(0x00, 4)
            for i, (data, err) in enumerate(data_list):
                print(f"Read[{i}] = 0x{data:08x}, error={err}")
        """
        addr_list = [start_addr + (i * 4) for i in range(num_reads)]
        op_list = [4] * num_reads  # All reads
        data_list = [0] * num_reads
        
        return await burst_sequence(self.driver, addr_list, op_list, data_list)
    
    async def burst_write(self, start_addr, data_list):
        """
        Perform a burst of consecutive write operations.
        
        Args:
            start_addr (int): Starting address (must be 4-byte aligned)
            data_list: List of write data values
            
        Returns:
            response_list: List of (None, error) tuples (None for writes)
            
        Example:
            await agent.burst_write(0x00, [0x1, 0x2, 0x3, 0x4])
        """
        addr_list = [start_addr + (i * 4) for i in range(len(data_list))]
        op_list = [0] * len(data_list)  # All writes
        
        return await burst_sequence(self.driver, addr_list, op_list, data_list)
    
    async def wait_for_ready(self, timeout_cycles=1000):
        """
        Wait for DUT to become ready after reset or initialization.
        
        Optional utility; mainly for synchronization before test starts.
        
        Args:
            timeout_cycles (int): Maximum cycles to wait
            
        Raises:
            TimeoutError: If DUT not ready within timeout
        """
        for _ in range(timeout_cycles):
            await RisingEdge(self.dut.clk_i)
            # Could add DUT-specific ready signal check here
        
        self.log.info("[TlUlAgent] DUT ready")
