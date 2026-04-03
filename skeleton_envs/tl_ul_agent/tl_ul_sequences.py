"""
TileLink-UL Helper Classes and Sequences

In UVM, "sequences" manage transaction generation and flow control.
In Cocotb/Python, we use simple async functions and helper classes instead.

Philosophy:
- No UVM sequencer/sequence infrastructure
- Helpers are simple Python functions or classes
- Tests call driver.drive_seq_item() directly with constructed items
- Transaction builders provide convenience for common operations (read, write, burst)
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
import random
from .tl_ul_seq_item import TlUlSeqItem


# ============================================================================
# TRANSACTION BUILDERS
# ============================================================================

class WriteOperation:
    """
    Helper for building a write transaction.
    
    Example:
        op = WriteOperation(addr=0x08, data=0xDEADBEEF)
        item = op.build()
        await driver.drive_seq_item(item)
    """
    
    def __init__(self, addr, data, mask=0xF, source=0, size=2):
        self.addr = addr
        self.data = data
        self.mask = mask
        self.source = source
        self.size = size
    
    def build(self):
        """Create and return TlUlSeqItem for this write."""
        return TlUlSeqItem(
            opcode=0,  # PutFullData
            address=self.addr,
            data=self.data,
            mask=self.mask,
            source=self.source,
            size=self.size,
            response_data=0,
            response_error=0
        )


class ReadOperation:
    """
    Helper for building a read transaction.
    
    Example:
        op = ReadOperation(addr=0x04)
        item = op.build()
        await driver.drive_seq_item(item)
        print(f"Read data: 0x{item.response_data:08x}")
    """
    
    def __init__(self, addr, source=0, size=2):
        self.addr = addr
        self.source = source
        self.size = size
    
    def build(self):
        """Create and return TlUlSeqItem for this read."""
        return TlUlSeqItem(
            opcode=4,  # Get (read)
            address=self.addr,
            data=0,
            mask=0xF,
            source=self.source,
            size=self.size,
            response_data=0,
            response_error=0
        )


# ============================================================================
# ASYNC GENERATORS FOR TRANSACTION STREAMS
# ============================================================================

async def write_sequence(driver, addr, data, mask=0xF):
    """
    Simple write sequence: Execute a single CSR write.
    
    Args:
        driver: TlUlDriver instance
        addr: Target address
        data: Write data
        mask: Byte enable mask (default 0xF = full write)
        
    Returns:
        response_error: 0 if success, 1 if device error
        
    Example:
        await write_sequence(driver, 0x08, 0xDEADBEEF)
    """
    item = WriteOperation(addr, data, mask).build()
    await driver.drive_seq_item(item)
    return item.response_error


async def read_sequence(driver, addr):
    """
    Simple read sequence: Execute a single CSR read.
    
    Args:
        driver: TlUlDriver instance
        addr: Target address
        
    Returns:
        (data, error) tuple: Read data and error flag
        
    Example:
        data, error = await read_sequence(driver, 0x04)
    """
    item = ReadOperation(addr).build()
    await driver.drive_seq_item(item)
    return (item.response_data, item.response_error)


async def burst_sequence(driver, addr_list, op_list, data_list):
    """
    Burst sequence: Execute multiple transactions in sequence.
    
    Args:
        driver: TlUlDriver instance
        addr_list: List of addresses
        op_list: List of opcodes (0=write, 4=read)
        data_list: List of write data (0 for reads)
        
    Returns:
        responses: List of (data, error) for read operations, None for writes
        
    Example:
        resp = await burst_sequence(
            driver,
            [0x00, 0x04, 0x08],
            [0,    4,    0   ],
            [0x11, 0,    0x22]
        )
    """
    responses = []
    
    for i, (addr, opcode, data) in enumerate(zip(addr_list, op_list, data_list)):
        item = TlUlSeqItem(
            opcode=opcode,
            address=addr,
            data=data,
            mask=0xF,
            source=i % 256,
            size=2,
            response_data=0,
            response_error=0
        )
        
        await driver.drive_seq_item(item)
        
        if opcode == 4:  # Read
            responses.append((item.response_data, item.response_error))
        else:  # Write
            responses.append(None)
    
    return responses


async def random_sequence(driver, num_ops=50, addr_min=0x00, addr_max=0x1C):
    """
    Random sequence: Generate randomized CSR access pattern.
    
    Args:
        driver: TlUlDriver instance
        num_ops: Number of random operations
        addr_min: Minimum address (inclusive)
        addr_max: Maximum address (exclusive)
        
    Returns:
        transactions: List of completed TlUlSeqItem objects
        
    Example:
        items = await random_sequence(driver, num_ops=100)
    """
    transactions = []
    
    for i in range(num_ops):
        # 60% writes, 40% reads
        opcode = random.choice([0, 0, 0, 4, 4])
        
        # Random address (aligned to 4-byte boundaries)
        addr = random.randint(
            addr_min // 4,
            (addr_max - 4) // 4
        ) * 4
        
        # Random data and mask
        data = random.randint(0, (1 << 32) - 1)
        mask = random.choice([0xF, 0xF, 0xF, 0x3, 0xC])
        
        item = TlUlSeqItem(
            opcode=opcode,
            address=addr,
            data=data,
            mask=mask,
            source=i % 256,
            size=2,
            response_data=0,
            response_error=0
        )
        
        await driver.drive_seq_item(item)
        transactions.append(item)
    
    return transactions


# ============================================================================
# LEGACY SEQUENCE CLASSES (for compatibility with old code)
# ============================================================================

class TlUlSequencer:
    """
    Placeholder sequencer class (for compatibility).
    
    In Cocotb/pure Python, sequencer logic is not needed.
    Tests interact directly with driver via async functions.
    This class is kept for source compatibility but is largely unused.
    """
    
    def __init__(self, name="tl_ul_sequencer", parent=None):
        self.name = name
        self.parent = parent


class TlUlWriteSeq:
    """
    Placeholder write sequence (for backward compatibility).
    
    Usage: See WriteOperation instead, or use write_sequence() helper.
    """
    
    def __init__(self, name="tl_ul_write_seq"):
        self.name = name
        self.addr = 0
        self.data = 0
        self.mask = 0xF
        self.source = 0
        self.size = 2
    
    def build(self):
        """Build underlying transaction"""
        return TlUlSeqItem(
            opcode=0,
            address=self.addr,
            data=self.data,
            mask=self.mask,
            source=self.source,
            size=self.size
        )


class TlUlReadSeq:
    """
    Placeholder read sequence (for backward compatibility).
    
    Usage: See ReadOperation instead, or use read_sequence() helper.
    """
    
    def __init__(self, name="tl_ul_read_seq"):
        self.name = name
        self.addr = 0
        self.rsp_data = 0
        self.rsp_error = 0
        self.source = 0
        self.size = 2
    
    def build(self):
        """Build underlying transaction"""
        return TlUlSeqItem(
            opcode=4,
            address=self.addr,
            data=0,
            mask=0xF,
            source=self.source,
            size=self.size
        )


class TlUlBurstSeq:
    """
    Placeholder burst sequence (for backward compatibility).
    
    Usage: See burst_sequence() async helper instead.
    """
    
    def __init__(self, name="tl_ul_burst_seq"):
        self.name = name
        self.addr_list = []
        self.op_list = []
        self.data_list = []
        self.responses = []


class TlUlRandomSeq:
    """
    Placeholder random sequence (for backward compatibility).
    
    Usage: See random_sequence() async helper instead.
    """
    
    def __init__(self, name="tl_ul_random_seq"):
        self.name = name
        self.num_ops = 50
        self.addr_min = 0x00
        self.addr_max = 0x1C
