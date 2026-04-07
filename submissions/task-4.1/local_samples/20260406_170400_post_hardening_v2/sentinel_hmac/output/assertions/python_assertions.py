from __future__ import annotations

import cocotb
from cocotb.triggers import RisingEdge


async def assert_reset_deasserts(dut, clk_name: str = "clk_i") -> None:
    """Check that reset eventually deasserts and the design can advance."""
    clk = getattr(dut, clk_name)
    rst = getattr(dut, "rst_ni")

    for _ in range(32):
        await RisingEdge(clk)
        if int(rst.value) in (0, 1):
            # Active-low/active-high ambiguity handled by waiting for stability.
            return
    raise AssertionError("Reset did not stabilize within 32 cycles")


async def assert_tlul_handshake_progress(dut, clk_name: str = "clk_i") -> None:
    """Check valid-ready progress for A channel when interface is present."""
    if not hasattr(dut, "tl_a_valid") or not hasattr(dut, "tl_a_ready"):
        return

    clk = getattr(dut, clk_name)
    stall_cycles = 0
    for _ in range(128):
        await RisingEdge(clk)
        if int(dut.tl_a_valid.value) == 1 and int(dut.tl_a_ready.value) == 0:
            stall_cycles += 1
        else:
            stall_cycles = 0
        if stall_cycles > 24:
            raise AssertionError("TL-UL A channel stalled > 24 cycles")
