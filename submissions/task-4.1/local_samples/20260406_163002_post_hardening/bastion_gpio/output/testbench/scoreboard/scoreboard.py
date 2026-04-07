from __future__ import annotations


class Scoreboard:
    """Simple scoreboard comparing expected and observed CSR reads."""

    def __init__(self) -> None:
        self.mismatches: list[str] = []

    def check_read(self, *, addr: int, expected: int, observed: int) -> None:
        if (expected & 0xFFFFFFFF) != (observed & 0xFFFFFFFF):
            self.mismatches.append(
                f"addr=0x{addr:08X} expected=0x{expected:08X} observed=0x{observed:08X}"
            )

    def assert_clean(self) -> None:
        assert not self.mismatches, "Scoreboard mismatches:\n" + "\n".join(self.mismatches)
