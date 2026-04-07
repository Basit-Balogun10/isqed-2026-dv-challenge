from __future__ import annotations


class CoverageCollector:
    """DUT-generic functional coverage with richer bin dimensions."""

    def __init__(self, register_addrs: list[int] | None = None) -> None:
        self.register_addrs = register_addrs or [0x0, 0x4, 0x8, 0xC, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C, 0x30, 0x34, 0x38]
        self.counters: dict[str, int] = {}
        self._define_bins()

    def _define_bins(self) -> None:
        static_bins = [
            "reset_sequence",
            "error_path",
            "operation_read",
            "operation_write",
            "operation_error",
        ]
        for name in static_bins:
            self.counters[name] = 0

        for op in ("read", "write"):
            for idx, _addr in enumerate(self.register_addrs):
                self.counters[f"op_{op}_reg_{idx:02d}"] = 0

        for region in ("low", "mid", "high"):
            for op in ("read", "write"):
                self.counters[f"op_{op}_region_{region}"] = 0

        for pattern in ("zero", "ones", "alternating", "sparse", "random"):
            self.counters[f"write_data_pattern_{pattern}"] = 0

        for region in ("low", "mid", "high"):
            for pattern in ("zero", "ones", "alternating", "sparse", "random"):
                self.counters[f"cross_write_region_{region}_pattern_{pattern}"] = 0

    def hit(self, bin_name: str) -> None:
        if bin_name in self.counters:
            self.counters[bin_name] += 1

    def _classify_addr_region(self, addr: int) -> str:
        if addr < 0x100:
            return "low"
        if addr < 0x400:
            return "mid"
        return "high"

    def _classify_data_pattern(self, data: int) -> str:
        value = int(data) & 0xFFFFFFFF
        if value == 0:
            return "zero"
        if value == 0xFFFFFFFF:
            return "ones"
        if value in (0xAAAAAAAA, 0x55555555):
            return "alternating"
        if value & (value - 1) == 0:
            return "sparse"
        return "random"

    def hit_operation(
        self,
        *,
        op: str,
        addr: int | None = None,
        data: int | None = None,
        error: bool = False,
    ) -> None:
        op_name = op.lower().strip()
        if op_name in ("read", "write"):
            self.hit(f"operation_{op_name}")
        if error:
            self.hit("operation_error")
            self.hit("error_path")

        if addr is not None:
            region = self._classify_addr_region(int(addr))
            if op_name in ("read", "write"):
                self.hit(f"op_{op_name}_region_{region}")

                for idx, reg_addr in enumerate(self.register_addrs):
                    if int(reg_addr) == int(addr):
                        self.hit(f"op_{op_name}_reg_{idx:02d}")
                        break

        if op_name == "write" and data is not None:
            pattern = self._classify_data_pattern(int(data))
            self.hit(f"write_data_pattern_{pattern}")
            if addr is not None:
                region = self._classify_addr_region(int(addr))
                self.hit(f"cross_write_region_{region}_pattern_{pattern}")

    def snapshot(self) -> dict[str, int]:
        return dict(self.counters)
