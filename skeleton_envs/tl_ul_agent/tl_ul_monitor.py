"""
TileLink-UL Monitor

Passively observes TL-UL traffic (A and D channels) and broadcasts complete
transactions to analysis port subscribers.

Philosophy:
- Pure Python class (not UVM uvm_monitor)
- Uses callback list instead of UVM analysis_port
- Runs as an async background task (cocotb.start_soon)
- Non-intrusive: only reads signals, never drives
"""

import cocotb
from cocotb.triggers import RisingEdge
from .tl_ul_seq_item import TlUlSeqItem


class TlUlMonitor:
    """
    Passive monitor for TL-UL bus transactions.
    
    Behavior:
    - Observes A-channel: When tl_a_valid & tl_a_ready, capture request metadata
    - Observes D-channel: When tl_d_valid & tl_d_ready, capture response
    - Correlates request/response using source field (assumes single-cycle latency)
    - Invokes callbacks for each complete transaction
    
    Philosophy:
    In UVM, we have analysis_port.write(item). In cocotb, we just use Python
    callbacks: `monitor.register_callback(my_callback_func)`.
    Each callback is called with the complete TlUlSeqItem.
    
    Typical Usage:
        monitor = TlUlMonitor(dut, log=dut._log)
        
        # In a test, start monitor as background task
        monitor_task = await cocotb.start(monitor.run())
        
        # Register callback (e.g., scoreboard)
        def scoreboard_callback(item):
            # Process transaction
            print(f"Monitored: {item}")
        
        monitor.register_callback(scoreboard_callback)
    """
    
    def __init__(self, dut, log=None):
        """
        Initialize monitor.
        
        Args:
            dut: Cocotb DUT handle
            log: Optional logger (uses dut._log by default)
        """
        self.dut = dut
        self.log = log or dut._log
        self.callbacks = []  # List of callback functions to invoke per transaction
        self.transaction_count = 0
    
    def register_callback(self, callback_func):
        """
        Register a function to be called for each monitored transaction.
        
        Args:
            callback_func: Async function or coroutine that takes TlUlSeqItem
            
        Example:
            async def my_scoreboard(item):
                await process(item)
            
            monitor.register_callback(my_scoreboard)
        """
        self.callbacks.append(callback_func)
        self.log.debug(f"[MonitorCallback] Registered callback: {callback_func.__name__}")
    
    async def run(self):
        """
        Main monitor loop: Capture and broadcast transactions.
        
        This coroutine runs continuously, monitoring the bus.
        Call as: `cocotb.start_soon(monitor.run())` to run in background.
        """
        # Track pending requests by source ID
        # Structure: {source_id: (opcode, address, data, mask)}
        pending_requests = {}
        
        self.log.info("[TlUlMonitor] Starting TL-UL bus monitor")
        
        while True:
            await RisingEdge(self.dut.clk_i)
            
            # ===== A-CHANNEL: Capture outgoing requests =====
            if int(self.dut.tl_a_valid_o.value) == 1 and \
               int(self.dut.tl_a_ready_i.value) == 1:
                
                source_id = int(self.dut.tl_a_source_o.value)
                opcode = int(self.dut.tl_a_opcode_o.value)
                address = int(self.dut.tl_a_address_o.value)
                data = int(self.dut.tl_a_data_o.value)
                mask = int(self.dut.tl_a_mask_o.value)
                size = int(self.dut.tl_a_size_o.value) if hasattr(self.dut, 'tl_a_size_o') else 2
                
                # Store for later correlation
                pending_requests[source_id] = {
                    'opcode': opcode,
                    'address': address,
                    'data': data,
                    'mask': mask,
                    'size': size
                }
                
                self.log.debug(
                    f"[MonitorA] Captured A-channel: source={source_id}, "
                    f"opcode={opcode}, addr=0x{address:08x}, data=0x{data:08x}"
                )
            
            # ===== D-CHANNEL: Capture responses and correlate with requests =====
            if int(self.dut.tl_d_valid_o.value) == 1 and \
               int(self.dut.tl_d_ready_i.value) == 1:
                
                source_id = int(self.dut.tl_d_source_o.value)
                response_data = int(self.dut.tl_d_data_o.value)
                response_error = int(self.dut.tl_d_error_o.value)
                
                # Look up the original request
                if source_id in pending_requests:
                    req = pending_requests.pop(source_id)
                    
                    # Build complete transaction
                    item = TlUlSeqItem(
                        opcode=req['opcode'],
                        address=req['address'],
                        data=req['data'],
                        mask=req['mask'],
                        source=source_id,
                        size=req['size'],
                        response_data=response_data,
                        response_error=response_error
                    )
                    
                    self.transaction_count += 1
                    
                    self.log.info(
                        f"[MonitorComplete] Transaction #{self.transaction_count}: "
                        f"addr=0x{item.address:08x}, "
                        f"rsp_data=0x{response_data:08x}, rsp_error={response_error}"
                    )
                    
                    # Invoke all registered callbacks
                    for callback in self.callbacks:
                        try:
                            # Check if callback is async
                            if cocotb.utils.xfail(lambda: callback(item), allow_exceptions=False):
                                # Sync callback
                                callback(item)
                            else:
                                # Async callback
                                await callback(item)
                        except Exception as e:
                            self.log.error(f"[MonitorCallback] Exception: {e}")
                else:
                    self.log.warning(
                        f"[MonitorD] Orphaned D-channel response (source={source_id}): "
                        f"no matching A-channel request. Skipping."
                    )
