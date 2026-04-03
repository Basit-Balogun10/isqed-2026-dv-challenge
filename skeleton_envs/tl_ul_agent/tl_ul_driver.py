"""
TileLink-UL Driver

Translates TlUlSeqItem transactions into actual TL-UL bus transactions.
Handles A-channel request handshaking and D-channel response capture.

Philosophy:
- This is a pure Python class (not UVM), designed for Cocotb
- No phases (build_phase, run_phase) - uses async methods called from tests
- Driven by direct method calls (drive_seq_item) rather than sequencer polling
- DUT reference injected by environment during setup
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from .tl_ul_seq_item import TlUlSeqItem


class TlUlDriver:
    """
    Drives TL-UL A and D channel transactions.
    
    Typical Usage (in a test):
        driver = TlUlDriver(dut)
        item = TlUlSeqItem(opcode=0, address=0x08, data=0xDEADBEEF, mask=0xF)
        await driver.drive_seq_item(item)
        print(f"Response: data=0x{item.response_data:08x}, error={item.response_error}")
    
    Key Responsibilities:
    - Drive A-channel signals when asked (opcode, address, data, mask, source, size)
    - Wait for tl_a_ready to accept the transaction
    - Wait for D-channel response (tl_d_valid)
    - Capture response data and error flag
    - Acknowledge response with tl_d_ready pulse
    - Populate seq_item with response_data and response_error
    """
    
    def __init__(self, dut, log=None, timeout_cycles=1000):
        """
        Initialize driver.
        
        Args:
            dut: Cocotb DUT handle (from cocotb.top)
            log: Optional logger (uses dut._log by default)
            timeout_cycles: Max cycles to wait for tl_a_ready or tl_d_valid
        """
        self.dut = dut
        self.log = log or dut._log
        self.timeout_cycles = timeout_cycles
    
    async def drive_seq_item(self, item):
        """
        Execute a single TL-UL transaction.
        
        Steps:
        1. Assert A-channel (opcode, address, data, mask, source, size, valid)
        2. Wait for tl_a_ready to accept request
        3. De-assert A-channel
        4. Wait for D-channel response (tl_d_valid)
        5. Capture response_data and response_error into item
        6. Pulse tl_d_ready to acknowledge
        
        Args:
            item: TlUlSeqItem to drive (modified in-place with response fields)
            
        Exceptions:
            TimeoutError: If A-channel or D-channel handshake times out
        """
        self.log.info(
            f"[TlUlDriver] Driving transaction: opcode={item.opcode}, "
            f"addr=0x{item.address:08x}, data=0x{item.data:08x}, mask=0x{item.mask:x}"
        )
        
        # Drive A-channel request
        await self._drive_a_channel(item)
        self.log.info(f"[TlUlDriver] A-channel accepted at cycle {self.dut.cocotb_simulator.cycle}")
        
        # Wait for D-channel response
        await self._wait_d_channel(item)
        self.log.info(
            f"[TlUlDriver] Transaction complete: "
            f"rsp_data=0x{item.response_data:08x}, rsp_error={item.response_error}"
        )
    
    async def _drive_a_channel(self, item):
        """
        Drive the A-channel with request data and wait for tl_a_ready.
        
        Timeline:
        - Cycle N: Set all A-channel signals including tl_a_valid=1
        - Cycle N+1..N+k: Hold until tl_a_ready=1
        - Cycle N+k+1: De-assert tl_a_valid and signals
        """
        # Drive A-channel request signals
        self.dut.tl_a_opcode_i.value = item.opcode
        self.dut.tl_a_address_i.value = item.address
        self.dut.tl_a_data_i.value = item.data
        self.dut.tl_a_mask_i.value = item.mask
        self.dut.tl_a_source_i.value = item.source
        self.dut.tl_a_size_i.value = item.size
        self.dut.tl_a_valid_i.value = 1  # Assert valid
        
        # Wait for acceptance (tl_a_ready handshake)
        for cycle in range(self.timeout_cycles):
            await RisingEdge(self.dut.clk_i)
            if int(self.dut.tl_a_ready_o.value) == 1:
                # Transaction accepted by DUT
                self.dut.tl_a_valid_i.value = 0  # De-assert valid after handshake
                await RisingEdge(self.dut.clk_i)  # One more cycle to clean up
                break
        else:
            # Timeout - no acceptance
            raise TimeoutError(
                f"A-channel timeout: tl_a_ready never asserted after {self.timeout_cycles} cycles. "
                f"Request: opcode={item.opcode}, addr=0x{item.address:08x}"
            )
        
        # De-assert all A-channel signals
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0
        self.dut.tl_a_data_i.value = 0
        self.dut.tl_a_mask_i.value = 0
        self.dut.tl_a_source_i.value = 0
        self.dut.tl_a_size_i.value = 0
    
    async def _wait_d_channel(self, item):
        """
        Wait for D-channel response and capture result.
        
        Timeline:
        - Cycle N: Poll tl_d_valid_o
        - Cycle N+k: tl_d_valid=1, capture response_data and response_error
        - Cycle N+k: Assert tl_d_ready=1 to acknowledge
        - Cycle N+k+1: De-assert tl_d_ready
        """
        # Initially, we're not ready for response
        self.dut.tl_d_ready_i.value = 0
        
        # Wait for tl_d_valid (response available)
        for cycle in range(self.timeout_cycles):
            await RisingEdge(self.dut.clk_i)
            if int(self.dut.tl_d_valid_o.value) == 1:
                # Response available - capture it
                item.response_data = int(self.dut.tl_d_data_o.value)
                item.response_error = int(self.dut.tl_d_error_o.value)
                
                # Acknowledge with tl_d_ready pulse
                self.dut.tl_d_ready_i.value = 1
                await RisingEdge(self.dut.clk_i)
                self.dut.tl_d_ready_i.value = 0
                
                return  # Success
        
        # Timeout - no response
        raise TimeoutError(
            f"D-channel timeout: tl_d_valid never asserted after {self.timeout_cycles} cycles. "
            f"Address: 0x{item.address:08x}"
        )
