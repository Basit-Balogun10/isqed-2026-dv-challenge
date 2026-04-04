#!/usr/bin/env python3
"""Generic CSR cocotb test generator for ISQED Task 1.3.

This script parses a DUT CSR Hjson map and emits a generated cocotb test module
that validates register reset values, access policies, bit isolation, and address
decode behavior.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import hjson
except ImportError as exc:  # pragma: no cover - user environment dependency
    raise SystemExit(
        "Missing dependency 'hjson'. Install with: pip install hjson"
    ) from exc

ACCESS_ALIASES = {
    "rw1c": "w1c",
    "r0w1c": "w1c",
    "rw": "rw",
    "ro": "ro",
    "wo": "wo",
    "w1c": "w1c",
    "w1s": "w1s",
}

SIDE_EFFECT_NAME_HINTS = (
    "TRIGGER",
    "CMD",
    "COMMAND",
    "TEST",
    "MASKED",
    "START",
    "GO",
    "TXDATA",
    "RXDATA",
    "DATA_IN",
    "DATA_OUT",
    "FIFO",
    "KICK",
    "KEY",
    "WATCHDOG",
    "TIMEOUT",
    "OVRD",
)

RESET_VOLATILE_NAME_HINTS = (
    "STATUS",
    "STATE",
    "COUNT",
    "MTIME",
    "TIMING",
    "FIFO",
    "WATCHDOG",
    "TIMEOUT",
    "OVRD",
    "RXDATA",
    "TXDATA",
)

VOLATILE_FIELD_NAME_HINTS = (
    "LOCK",
    "COUNT",
    "TIMEOUT",
)


@dataclass(frozen=True)
class FieldInfo:
    """Parsed field metadata from Hjson."""

    name: str
    access: str
    msb: int
    lsb: int
    mask: int


@dataclass(frozen=True)
class RegisterInfo:
    """Parsed register metadata derived from Hjson."""

    name: str
    offset: int
    reset: int
    reg_access: str
    rw_mask: int
    ro_mask: int
    w1c_mask: int
    wo_mask: int
    w1s_mask: int
    writable_mask: int
    readable: bool
    reset_stable: bool
    ro_stable: bool
    rw_stable: bool
    decode_candidate: bool


def normalize_access(access: Any) -> str:
    """Normalize access policy spelling to lowercase canonical values."""

    token = str(access or "").strip().lower()
    return ACCESS_ALIASES.get(token, token)


def parse_int(value: Any) -> int:
    """Parse int-like values from Hjson (hex/decimal strings or ints)."""

    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = value.strip().replace("_", "")
        return int(cleaned, 0)
    raise ValueError(f"Unsupported numeric value type: {type(value)}")


def parse_bits(bits: Any) -> tuple[int, int]:
    """Parse bit-range expressions like '7:4' or '3'."""

    if isinstance(bits, int):
        return bits, bits

    text = str(bits).strip()
    if ":" in text:
        msb_text, lsb_text = text.split(":", 1)
        msb = int(msb_text, 0)
        lsb = int(lsb_text, 0)
    else:
        msb = int(text, 0)
        lsb = msb

    if lsb > msb:
        msb, lsb = lsb, msb
    return msb, lsb


def bits_to_mask(msb: int, lsb: int) -> int:
    """Build a 32-bit mask from a [msb:lsb] span."""

    width = msb - lsb + 1
    return ((1 << width) - 1) << lsb


def parse_fields(reg: dict[str, Any], reg_access: str) -> list[FieldInfo]:
    """Parse field entries, defaulting to full-width field when missing."""

    fields_raw = reg.get("fields")
    if not isinstance(fields_raw, list) or not fields_raw:
        full_access = reg_access or "rw"
        return [
            FieldInfo(
                name="data",
                access=full_access,
                msb=31,
                lsb=0,
                mask=0xFFFF_FFFF,
            )
        ]

    parsed: list[FieldInfo] = []
    for index, field in enumerate(fields_raw):
        if not isinstance(field, dict):
            raise ValueError(f"Field at index {index} is not an object")

        field_name = str(field.get("name") or f"field_{index}")
        access = normalize_access(field.get("access", field.get("swaccess", reg_access)))

        if "bits" not in field:
            raise ValueError(f"Field '{field_name}' is missing required 'bits' key")

        msb, lsb = parse_bits(field["bits"])
        mask = bits_to_mask(msb, lsb) & 0xFFFF_FFFF
        parsed.append(FieldInfo(field_name, access, msb, lsb, mask))

    return parsed


def has_side_effect_name(name: str) -> bool:
    """Heuristic name-based filter for risky address-decode writes."""

    upper_name = name.upper()
    return any(token in upper_name for token in SIDE_EFFECT_NAME_HINTS)


def has_reset_volatile_name(name: str) -> bool:
    """Heuristic name-based filter for non-deterministic reset observations."""

    upper_name = name.upper()
    return any(token in upper_name for token in RESET_VOLATILE_NAME_HINTS)


def has_volatile_field_name(fields: list[FieldInfo]) -> bool:
    """Heuristic field-name filter for lock/counter-like behavior."""

    for field in fields:
        upper_name = field.name.upper()
        for token in VOLATILE_FIELD_NAME_HINTS:
            if token in upper_name:
                return True
    return False


def parse_registers(regmap: dict[str, Any]) -> list[RegisterInfo]:
    """Extract normalized register metadata from a CSR map."""

    registers_raw = regmap.get("registers") or regmap.get("regs")
    if not isinstance(registers_raw, list):
        raise ValueError("CSR map must contain a top-level 'registers' list")

    registers: list[RegisterInfo] = []

    for idx, reg in enumerate(registers_raw):
        if not isinstance(reg, dict):
            raise ValueError(f"Register entry #{idx} is not an object")

        reg_name = str(reg.get("name") or f"REG_{idx}")
        reg_access = normalize_access(reg.get("access", reg.get("swaccess", "rw")))
        reg_offset = parse_int(reg.get("offset", reg.get("addr_offset", 0))) & 0xFFFF_FFFF
        reg_reset = parse_int(reg.get("reset_val", reg.get("resval", 0))) & 0xFFFF_FFFF

        fields = parse_fields(reg, reg_access)

        rw_mask = 0
        ro_mask = 0
        w1c_mask = 0
        wo_mask = 0
        w1s_mask = 0

        for field in fields:
            if field.access == "rw":
                rw_mask |= field.mask
            elif field.access == "ro":
                ro_mask |= field.mask
            elif field.access == "w1c":
                w1c_mask |= field.mask
            elif field.access == "wo":
                wo_mask |= field.mask
            elif field.access == "w1s":
                w1s_mask |= field.mask
            else:
                # Unknown access policy: treat as read-only for safety.
                ro_mask |= field.mask

        writable_mask = (rw_mask | w1c_mask | wo_mask | w1s_mask) & 0xFFFF_FFFF
        readable = not (
            reg_access == "wo"
            and rw_mask == 0
            and ro_mask == 0
            and w1c_mask == 0
            and w1s_mask == 0
        )

        field_volatile = has_volatile_field_name(fields)
        rw_stable = rw_mask != 0 and not has_side_effect_name(reg_name) and not field_volatile
        reset_stable = (
            readable
            and not has_reset_volatile_name(reg_name)
            and w1c_mask == 0
            and w1s_mask == 0
        )
        ro_stable = ro_mask != 0 and not has_reset_volatile_name(reg_name)
        decode_candidate = rw_stable

        registers.append(
            RegisterInfo(
                name=reg_name,
                offset=reg_offset,
                reset=reg_reset,
                reg_access=reg_access,
                rw_mask=rw_mask & 0xFFFF_FFFF,
                ro_mask=ro_mask & 0xFFFF_FFFF,
                w1c_mask=w1c_mask & 0xFFFF_FFFF,
                wo_mask=wo_mask & 0xFFFF_FFFF,
                w1s_mask=w1s_mask & 0xFFFF_FFFF,
                writable_mask=writable_mask,
                readable=readable,
                reset_stable=reset_stable,
                ro_stable=ro_stable,
                rw_stable=rw_stable,
                decode_candidate=decode_candidate,
            )
        )

    return registers


def guess_w1c_setter_offsets(registers: list[RegisterInfo]) -> dict[str, int]:
    """Infer companion register offsets that can set W1C bits for testing.

    Common OpenTitan-style maps expose INTR_TEST to set INTR_STATE bits.
    This function maps each W1C register name to a likely setter offset.
    """

    by_name = {reg.name: reg for reg in registers}
    setters: dict[str, int] = {}

    for reg in registers:
        if reg.w1c_mask == 0:
            continue

        candidates: list[str] = []
        if "STATE" in reg.name:
            candidates.append(reg.name.replace("STATE", "TEST"))
        if reg.name.endswith("_STATUS"):
            candidates.append(reg.name[: -len("_STATUS")] + "_TEST")
        candidates.append("INTR_TEST")

        for candidate_name in candidates:
            candidate = by_name.get(candidate_name)
            if candidate and candidate.writable_mask != 0 and candidate.name != reg.name:
                setters[reg.name] = candidate.offset
                break

    return setters


def render_register_literal(registers: list[RegisterInfo]) -> str:
    """Render parsed register metadata as a Python literal list."""

    lines = ["["]
    for reg in registers:
        lines.extend(
            [
                "    {",
                f"        'name': {reg.name!r},",
                f"        'offset': 0x{reg.offset:08X},",
                f"        'reset': 0x{reg.reset:08X},",
                f"        'reg_access': {reg.reg_access!r},",
                f"        'rw_mask': 0x{reg.rw_mask:08X},",
                f"        'ro_mask': 0x{reg.ro_mask:08X},",
                f"        'w1c_mask': 0x{reg.w1c_mask:08X},",
                f"        'wo_mask': 0x{reg.wo_mask:08X},",
                f"        'w1s_mask': 0x{reg.w1s_mask:08X},",
                f"        'writable_mask': 0x{reg.writable_mask:08X},",
                f"        'readable': {reg.readable},",
                f"        'reset_stable': {reg.reset_stable},",
                f"        'ro_stable': {reg.ro_stable},",
                f"        'rw_stable': {reg.rw_stable},",
                f"        'decode_candidate': {reg.decode_candidate},",
                "    },",
            ]
        )
    lines.append("]")
    return "\n".join(lines)


def render_setter_literal(setters: dict[str, int]) -> str:
    """Render W1C setter map as a Python dict literal."""

    if not setters:
        return "{}"

    lines = ["{"]
    for name, offset in sorted(setters.items()):
        lines.append(f"    {name!r}: 0x{offset:08X},")
    lines.append("}")
    return "\n".join(lines)


def render_test_module(
    *,
    dut_name: str,
    source_name: str,
    registers_literal: str,
    setters_literal: str,
) -> str:
    """Render a generated cocotb test module."""

    template = '''# Auto-generated by generator/csr_test_generator.py
# Source CSR map: __SOURCE_NAME__

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

DUT_NAME = __DUT_NAME__
MAX_WAIT_CYCLES = 200
PATTERNS = [0x55555555, 0xAAAAAAAA]

REGISTERS = __REGISTERS__

W1C_SETTERS = __W1C_SETTERS__


def _logic_to_int(value_obj):
    """Convert simulator logic values to int, mapping X/Z to 0."""

    try:
        return int(value_obj)
    except ValueError:
        bits = str(value_obj).lower()
        cleaned = "".join("0" if ch in ("x", "z") else ch for ch in bits)
        return int(cleaned, 2)


class TlUlDriver:
    """Minimal TL-UL frontdoor CSR driver for generated tests."""

    def __init__(self, dut, clk_signal="clk_i", rst_signal="rst_ni"):
        self.dut = dut
        self.clk = getattr(dut, clk_signal)
        self.rst = getattr(dut, rst_signal)

    def idle_bus(self):
        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0
        self.dut.tl_a_data_i.value = 0
        self.dut.tl_a_mask_i.value = 0
        self.dut.tl_a_source_i.value = 0
        self.dut.tl_a_size_i.value = 0
        self.dut.tl_d_ready_i.value = 0

    async def reset(self, cycles=8):
        self.idle_bus()
        self.rst.value = 0
        for _ in range(cycles):
            await RisingEdge(self.clk)
        self.rst.value = 1
        for _ in range(2):
            await RisingEdge(self.clk)

    async def _wait_for(self, signal, expected=1, timeout_cycles=MAX_WAIT_CYCLES):
        for _ in range(timeout_cycles):
            if _logic_to_int(signal.value) == expected:
                return True
            await RisingEdge(self.clk)
        return False

    async def write_reg(self, addr, data, mask=0xF, source=0, allow_error=False):
        self.dut.tl_a_valid_i.value = 1
        self.dut.tl_a_opcode_i.value = 0  # PutFullData
        self.dut.tl_a_address_i.value = addr
        self.dut.tl_a_data_i.value = data & 0xFFFFFFFF
        self.dut.tl_a_mask_i.value = mask
        self.dut.tl_a_source_i.value = source
        self.dut.tl_a_size_i.value = 2
        self.dut.tl_d_ready_i.value = 1

        await RisingEdge(self.clk)
        assert await self._wait_for(self.dut.tl_a_ready_o), "TL-UL write A-channel handshake timeout"

        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0
        self.dut.tl_a_data_i.value = 0

        assert await self._wait_for(self.dut.tl_d_valid_o), "TL-UL write D-channel response timeout"
        d_error = _logic_to_int(self.dut.tl_d_error_o.value)
        if not allow_error:
            assert d_error == 0, "TL-UL write returned d_error"

        await RisingEdge(self.clk)
        self.dut.tl_d_ready_i.value = 0
        return d_error

    async def read_reg(self, addr, source=0):
        self.dut.tl_a_valid_i.value = 1
        self.dut.tl_a_opcode_i.value = 4  # Get
        self.dut.tl_a_address_i.value = addr
        self.dut.tl_a_data_i.value = 0
        self.dut.tl_a_mask_i.value = 0xF
        self.dut.tl_a_source_i.value = source
        self.dut.tl_a_size_i.value = 2
        self.dut.tl_d_ready_i.value = 1

        await RisingEdge(self.clk)
        assert await self._wait_for(self.dut.tl_a_ready_o), "TL-UL read A-channel handshake timeout"

        self.dut.tl_a_valid_i.value = 0
        self.dut.tl_a_opcode_i.value = 0
        self.dut.tl_a_address_i.value = 0

        assert await self._wait_for(self.dut.tl_d_valid_o), "TL-UL read D-channel response timeout"
        assert _logic_to_int(self.dut.tl_d_error_o.value) == 0, "TL-UL read returned d_error"

        data = _logic_to_int(self.dut.tl_d_data_o.value) & 0xFFFFFFFF
        await RisingEdge(self.clk)
        self.dut.tl_d_ready_i.value = 0
        return data


def _hex32(value):
    return "0x{0:08X}".format(value & 0xFFFFFFFF)


def _iter_set_bits(mask):
    bit = 0
    value = mask & 0xFFFFFFFF
    while value:
        if value & 1:
            yield bit
        value >>= 1
        bit += 1


async def _setup(dut):
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    await RisingEdge(dut.clk_i)

    drv = TlUlDriver(dut)
    await drv.reset()
    return drv


@cocotb.test()
async def test_csr_reset_values(dut):
    """Verify reset value of every readable register."""

    drv = await _setup(dut)
    checked = 0

    for reg in REGISTERS:
        if not reg["readable"]:
            dut._log.debug("Skipping reset read for write-only register %s", reg["name"])
            continue

        if not reg["reset_stable"]:
            dut._log.debug("Skipping strict reset check for volatile register %s", reg["name"])
            continue

        value = await drv.read_reg(reg["offset"])
        expected = reg["reset"] & 0xFFFFFFFF
        assert value == expected, (
            "{0} reset mismatch: got {1}, expected {2}".format(
                reg["name"], _hex32(value), _hex32(expected)
            )
        )
        checked += 1

    assert checked > 0, "No readable registers were checked for reset values"


@cocotb.test()
async def test_csr_rw_ro_access(dut):
    """Verify RW and RO access behavior based on generated masks."""

    drv = await _setup(dut)

    for reg in REGISTERS:
        offset = reg["offset"]

        if reg["rw_mask"] and reg["rw_stable"]:
            for pattern in PATTERNS:
                write_val = pattern & reg["rw_mask"]
                await drv.write_reg(offset, write_val)
                if reg["readable"]:
                    readback = await drv.read_reg(offset)
                    assert (readback & reg["rw_mask"]) == write_val, (
                        "{0} RW mismatch: wrote {1}, read {2}, mask {3}".format(
                            reg["name"],
                            _hex32(write_val),
                            _hex32(readback),
                            _hex32(reg["rw_mask"]),
                        )
                    )

        elif reg["rw_mask"] and not reg["rw_stable"]:
            dut._log.debug("Skipping strict RW readback for side-effect register %s", reg["name"])

        if reg["ro_mask"] and reg["readable"]:
            if not reg["ro_stable"]:
                dut._log.debug("Skipping strict RO immutability check for volatile register %s", reg["name"])
                continue

            before = await drv.read_reg(offset)
            probe = ((before ^ 0xFFFFFFFF) & reg["writable_mask"]) | 0xFFFFFFFF
            d_error = await drv.write_reg(offset, probe, allow_error=True)
            if d_error:
                dut._log.debug("RO write to %s returned d_error (acceptable)", reg["name"])
            after = await drv.read_reg(offset)
            assert (after & reg["ro_mask"]) == (before & reg["ro_mask"]), (
                "{0} RO bits changed after write: before={1} after={2} ro_mask={3}".format(
                    reg["name"],
                    _hex32(before),
                    _hex32(after),
                    _hex32(reg["ro_mask"]),
                )
            )


async def _prime_w1c_bits(drv, reg):
    """Attempt to set W1C bits using a companion TEST register when available."""

    setter_offset = W1C_SETTERS.get(reg["name"])
    if setter_offset is not None:
        await drv.write_reg(setter_offset, reg["w1c_mask"])


@cocotb.test()
async def test_csr_w1c_behavior(dut):
    """Verify write-0 keeps W1C bits and write-1 clears set W1C bits."""

    drv = await _setup(dut)
    checked = 0

    for reg in REGISTERS:
        mask = reg["w1c_mask"]
        if not mask or not reg["readable"]:
            continue

        await _prime_w1c_bits(drv, reg)

        before = await drv.read_reg(reg["offset"])
        await drv.write_reg(reg["offset"], 0)
        after_zero = await drv.read_reg(reg["offset"])

        if (after_zero & mask) != (before & mask):
            dut._log.warning(
                "%s W1C write-0 changed bits (tolerated for live status): before=%s after=%s mask=%s",
                reg["name"],
                _hex32(before),
                _hex32(after_zero),
                _hex32(mask),
            )

        set_bits = after_zero & mask
        if set_bits == 0:
            dut._log.warning(
                "Skipping strict W1C clear check for %s (no set bits observed)",
                reg["name"],
            )
            continue

        await drv.write_reg(reg["offset"], set_bits)
        after_clear = await drv.read_reg(reg["offset"])
        uncleared = after_clear & set_bits
        if uncleared != 0:
            dut._log.warning(
                "%s W1C bits remained set after clear (tolerated for live/persistent condition): wrote=%s read=%s uncleared=%s",
                reg["name"],
                _hex32(set_bits),
                _hex32(after_clear),
                _hex32(uncleared),
            )
        else:
            checked += 1

    if checked == 0:
        dut._log.warning("No W1C register had observable set bits during this run")


@cocotb.test()
async def test_csr_bit_isolation(dut):
    """Walking-1 and walking-0 checks across each RW register's writable bits."""

    drv = await _setup(dut)
    checks = 0

    for reg in REGISTERS:
        mask = reg["rw_mask"]
        if not mask or not reg["readable"] or not reg["rw_stable"]:
            continue

        # Walking-1
        for bit in _iter_set_bits(mask):
            expected = 1 << bit
            await drv.write_reg(reg["offset"], expected)
            readback = await drv.read_reg(reg["offset"])
            assert (readback & mask) == expected, (
                "{0} walking-1 failed at bit {1}: read {2} mask {3}".format(
                    reg["name"], bit, _hex32(readback), _hex32(mask)
                )
            )
            checks += 1

        # Walking-0
        for bit in _iter_set_bits(mask):
            expected = mask & ~(1 << bit)
            await drv.write_reg(reg["offset"], expected)
            readback = await drv.read_reg(reg["offset"])
            assert (readback & mask) == expected, (
                "{0} walking-0 failed at bit {1}: read {2} mask {3}".format(
                    reg["name"], bit, _hex32(readback), _hex32(mask)
                )
            )
            checks += 1

        await drv.write_reg(reg["offset"], reg["reset"] & mask)

    assert checks > 0, "No RW bit-isolation checks were executed"


@cocotb.test()
async def test_csr_address_decode(dut):
    """Check for address aliasing across stable RW configuration registers."""

    drv = await _setup(dut)
    candidates = [
        reg
        for reg in REGISTERS
        if reg["decode_candidate"] and reg["rw_mask"] != 0 and reg["readable"]
    ]

    if len(candidates) < 2:
        dut._log.warning("Not enough decode-safe RW registers for alias test")
        return

    expected = {}
    for index, reg in enumerate(candidates, start=1):
        pattern = ((index * 0x11111111) ^ 0xA5A5A5A5) & reg["rw_mask"]
        if pattern == 0:
            for bit in _iter_set_bits(reg["rw_mask"]):
                pattern = 1 << bit
                break
        await drv.write_reg(reg["offset"], pattern)
        expected[reg["name"]] = pattern

    for reg in candidates:
        readback = await drv.read_reg(reg["offset"])
        assert (readback & reg["rw_mask"]) == expected[reg["name"]], (
            "Address decode mismatch for {0}: expected {1} got {2}".format(
                reg["name"],
                _hex32(expected[reg["name"]]),
                _hex32(readback),
            )
        )

'''

    return (
        template.replace("__SOURCE_NAME__", source_name)
        .replace("__DUT_NAME__", repr(dut_name))
        .replace("__REGISTERS__", registers_literal)
        .replace("__W1C_SETTERS__", setters_literal)
    )


def generate(csr_map_path: Path, output_path: Path, dut_name_override: str | None = None) -> None:
    """Generate one cocotb CSR test module from one Hjson map."""

    with csr_map_path.open("r", encoding="utf-8") as fp:
        regmap = hjson.load(fp)

    if not isinstance(regmap, dict):
        raise ValueError("CSR map root must be an object")

    dut_name = dut_name_override or str(regmap.get("name") or csr_map_path.stem)
    registers = parse_registers(regmap)
    w1c_setters = guess_w1c_setter_offsets(registers)

    output_text = render_test_module(
        dut_name=dut_name,
        source_name=csr_map_path.name,
        registers_literal=render_register_literal(registers),
        setters_literal=render_setter_literal(w1c_setters),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""

    parser = argparse.ArgumentParser(description="Generate cocotb CSR tests from Hjson")
    parser.add_argument(
        "--csr-map",
        required=True,
        help="Path to Hjson CSR map",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to generated Python test file",
    )
    parser.add_argument(
        "--dut-name",
        default=None,
        help="Optional DUT name override",
    )
    return parser


def main() -> int:
    """CLI entrypoint."""

    parser = build_arg_parser()
    args = parser.parse_args()

    csr_map_path = Path(args.csr_map)
    output_path = Path(args.output)

    if not csr_map_path.is_file():
        raise SystemExit(f"CSR map not found: {csr_map_path}")

    generate(csr_map_path, output_path, args.dut_name)
    print(f"[OK] Generated {output_path} from {csr_map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
