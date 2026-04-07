from __future__ import annotations

from typing import Any


class ProtocolAgent:
    """Protocol-side agent placeholder selected from ANALYZE-stage hints."""

    def __init__(self, dut: Any, protocol: str = "spi") -> None:
        self.dut = dut
        self.protocol = protocol

    async def configure_default(self) -> None:
        # Intentionally lightweight to remain generic across unseen DUTs.
        return

    async def drive_idle(self) -> None:
        return
