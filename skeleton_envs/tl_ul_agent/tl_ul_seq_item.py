"""
TileLink-UL Sequence Item

Represents a single CSR transaction (read or write) over the TL-UL bus interface.
All 7 DUTs share this transaction format.

For Path A (cocotb/Python-only), this is a plain Python dataclass, not UVM.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TlUlSeqItem:
    """
    Encapsulates a TL-UL CSR operation with request and response fields.
    
    -- REQUEST SIDE --
    opcode: 3-bit opcode
        - 0: PutFullData (write all bytes)
        - 1: PutPartial (write with mask)
        - 4: Get (read)
    
    address: 32-bit byte address
    data: 32-bit write data (ignored on reads)
    mask: 4-bit byte enable mask (e.g., 0xF = full, 0x3 = lower 16 bits)
    source: 8-bit transaction ID (for tracking responses)
    size: 2-bit size encoding (typically 2 for 32-bit transfers)
    
    -- RESPONSE SIDE --
    response_data: 32-bit read data (valid only on read responses)
    response_error: 1-bit error flag (device error, unmapped address, etc.)
    """
    
    opcode: int = 0  # 0=PutFull, 1=PutPartial, 4=Get
    address: int = 0  # 32-bit address
    data: int = 0  # 32-bit write data
    mask: int = 0xF  # 4-bit byte enable mask
    source: int = 0  # Transaction source ID
    size: int = 2  # 2^2 = 4 bytes = 32 bits
    response_data: int = 0  # Response data from DUT
    response_error: int = 0  # Response error flag
    _id_: int = field(default=0)  # Transaction ID for tracking
    
    def __str__(self):
        """Human-readable transaction summary."""
        if self.opcode == 0 or self.opcode == 1:
            # Write operation
            op_str = "PutFullData" if self.opcode == 0 else "PutPartial"
            return (f"TL-UL_{op_str} | addr=0x{self.address:08x} "
                    f"data=0x{self.data:08x} mask=0x{self.mask:x}")
        elif self.opcode == 4:
            # Read operation
            return (f"TL-UL_Get | addr=0x{self.address:08x} "
                    f"rsp_data=0x{self.response_data:08x} err={self.response_error}")
        else:
            return f"TL-UL_Unknown(opcode={self.opcode})"
    
    def copy(self):
        """Deep copy for cloning transactions."""
        return TlUlSeqItem(
            opcode=self.opcode,
            address=self.address,
            data=self.data,
            mask=self.mask,
            source=self.source,
            size=self.size,
            response_data=self.response_data,
            response_error=self.response_error,
            _id_=self._id_
        )
    
    def equals(self, rhs):
        """Compare two transactions for equality."""
        return (self.opcode == rhs.opcode and
                self.address == rhs.address and
                self.data == rhs.data and
                self.mask == rhs.mask and
                self.response_data == rhs.response_data and
                self.response_error == rhs.response_error)
