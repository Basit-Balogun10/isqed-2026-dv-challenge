from __future__ import annotations


class ReferenceModel:
    """Reference model tracks CSR values and predicts readback behavior."""

    def __init__(self) -> None:
        self.csr_mirror: dict[int, int] = {}

    def apply_reset(self) -> None:
        self.csr_mirror.clear()

    def write(self, addr: int, data: int) -> None:
        self.csr_mirror[addr] = data & 0xFFFFFFFF

    def read(self, addr: int) -> int:
        return self.csr_mirror.get(addr, 0)
