"""
TileLink-UL Agent Package

Provides reusable CSR transaction agent for all 7 DUTs in the ISQED 2026 challenge.
All DUTs use the same TL-UL interface, so this agent is shared across the design.

Key Components:
- TlUlSeqItem: Transaction item definition
- TlUlDriver: Handles A/D channel handshaking
- TlUlMonitor: Passive traffic capture with callback support
- TlUlAgent: Integrated agent with high-level CSR helper methods

Sequences & Helpers:
- write_sequence, read_sequence, burst_sequence, random_sequence: Async generators
- WriteOperation, ReadOperation: Transaction builders

Philosophy:
- Pure Python/Cocotb (no UVM)
- Callback-based monitoring (instead of UVM analysis_port)
- Async/await patterns throughout
- Direct method calls (not phase-based like UVM)
"""

# Core transaction item
from .tl_ul_seq_item import TlUlSeqItem

# Driver and monitor
from .tl_ul_driver import TlUlDriver
from .tl_ul_monitor import TlUlMonitor

# Agent (main entry point)
from .tl_ul_agent import TlUlAgent

# Sequences and helpers
from .tl_ul_sequences import (
    write_sequence,
    read_sequence,
    burst_sequence,
    random_sequence,
    WriteOperation,
    ReadOperation,
    TlUlSequencer,  # Legacy compatibility
    TlUlWriteSeq,   # Legacy compatibility
    TlUlReadSeq,    # Legacy compatibility
    TlUlBurstSeq,   # Legacy compatibility
    TlUlRandomSeq,  # Legacy compatibility
)

__all__ = [
    "TlUlSeqItem",
    "TlUlDriver",
    "TlUlMonitor",
    "TlUlAgent",
    "write_sequence",
    "read_sequence",
    "burst_sequence",
    "random_sequence",
    "WriteOperation",
    "ReadOperation",
    "TlUlSequencer",
    "TlUlWriteSeq",
    "TlUlReadSeq",
    "TlUlBurstSeq",
    "TlUlRandomSeq",
]
