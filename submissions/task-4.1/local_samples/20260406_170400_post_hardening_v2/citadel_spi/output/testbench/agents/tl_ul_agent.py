from __future__ import annotations

from typing import Any

import cocotb
from cocotb.triggers import RisingEdge


class TlUlDriver:
    """Reusable TL-UL CSR driver with dynamic signal lookup."""

    def __init__(self, dut: Any, clk_signal: str = "clk_i", rst_signal: str = "rst_ni") -> None:
        self.dut = dut
        self.clk = getattr(dut, clk_signal)
        self.rst = getattr(dut, rst_signal)

    def _set_if_present(self, name: str, value: int) -> None:
        sig = getattr(self.dut, name, None)
        if sig is not None:
            sig.value = value

    def _get_if_present(self, name: str, default: int = 0) -> int:
        sig = getattr(self.dut, name, None)
        if sig is None:
            return default
        try:
            return int(sig.value)
        except Exception:
            return default

    async def apply_reset(self, cycles: int = 5) -> None:
        # Supports active-low and active-high reset naming patterns.
        active_low = self.rst._name.lower().endswith("n")
        self.rst.value = 0 if active_low else 1
        for _ in range(max(1, cycles)):
            await RisingEdge(self.clk)
        self.rst.value = 1 if active_low else 0
        await RisingEdge(self.clk)

    async def csr_write(self, addr: int, data: int, mask: int = 0xF, timeout_cycles: int = 100) -> dict:
        self._set_if_present("tl_a_valid", 1)
        self._set_if_present("tl_a_opcode", 0)
        self._set_if_present("tl_a_address", addr)
        self._set_if_present("tl_a_data", data)
        self._set_if_present("tl_a_mask", mask)
        self._set_if_present("tl_a_size", 2)

        for _ in range(timeout_cycles):
            await RisingEdge(self.clk)
            if self._get_if_present("tl_a_ready", 1):
                break

        self._set_if_present("tl_a_valid", 0)

        self._set_if_present("tl_d_ready", 1)
        for _ in range(timeout_cycles):
            await RisingEdge(self.clk)
            if self._get_if_present("tl_d_valid", 1):
                break

        return {
            "error": self._get_if_present("tl_d_error", 0),
            "data": self._get_if_present("tl_d_data", 0),
        }

    async def csr_read(self, addr: int, mask: int = 0xF, timeout_cycles: int = 100) -> dict:
        self._set_if_present("tl_a_valid", 1)
        self._set_if_present("tl_a_opcode", 4)
        self._set_if_present("tl_a_address", addr)
        self._set_if_present("tl_a_mask", mask)
        self._set_if_present("tl_a_size", 2)

        for _ in range(timeout_cycles):
            await RisingEdge(self.clk)
            if self._get_if_present("tl_a_ready", 1):
                break

        self._set_if_present("tl_a_valid", 0)

        self._set_if_present("tl_d_ready", 1)
        for _ in range(timeout_cycles):
            await RisingEdge(self.clk)
            if self._get_if_present("tl_d_valid", 1):
                break

        return {
            "error": self._get_if_present("tl_d_error", 0),
            "data": self._get_if_present("tl_d_data", 0),
        }


class TlUlMonitor:
    """Minimal monitor placeholder to extend with protocol-level analysis."""

    def __init__(self, dut: Any) -> None:
        self.dut = dut
        self.samples: list[dict] = []

    def sample(self) -> None:
        self.samples.append({
            "a_valid": int(getattr(self.dut, "tl_a_valid", 0).value) if hasattr(self.dut, "tl_a_valid") else 0,
            "a_ready": int(getattr(self.dut, "tl_a_ready", 0).value) if hasattr(self.dut, "tl_a_ready") else 0,
            "d_valid": int(getattr(self.dut, "tl_d_valid", 0).value) if hasattr(self.dut, "tl_d_valid") else 0,
            "d_ready": int(getattr(self.dut, "tl_d_ready", 0).value) if hasattr(self.dut, "tl_d_ready") else 0,
        })
