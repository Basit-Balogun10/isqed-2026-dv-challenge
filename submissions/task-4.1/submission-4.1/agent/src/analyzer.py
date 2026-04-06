from __future__ import annotations

import re
from pathlib import Path

from io_utils import discover_rtl_files, read_text

_MODULE_RE = re.compile(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)")
_PORT_RE = re.compile(
    r"\b(input|output|inout)\b\s*(?:logic|wire|reg)?\s*(\[[^\]]+\])?\s*([A-Za-z_][A-Za-z0-9_]*)"
)
_ENUM_RE = re.compile(
    r"typedef\s+enum(?:\s+[A-Za-z_][A-Za-z0-9_]*)?\s*\{([\s\S]*?)\}\s*([A-Za-z_][A-Za-z0-9_]*)\s*;",
    flags=re.MULTILINE,
)
_CASE_RE = re.compile(
    r"\bcase\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)([\s\S]*?)\bendcase\b",
    flags=re.MULTILINE,
)
_CASE_LABEL_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", flags=re.MULTILINE)
_NEXT_ASSIGN_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:<=|=)\s*([A-Za-z_][A-Za-z0-9_]*)\b"
)


def _parse_csr_map(csr_map_path: Path) -> dict:
    text = read_text(csr_map_path)
    if not text:
        return {"register_count": 0, "top_keys": []}

    try:
        import hjson  # type: ignore[import-untyped]

        data = hjson.loads(text)
    except Exception:
        data = {}

    if isinstance(data, dict):
        keys = list(data.keys())[:20]
        regs_raw = data.get("registers")
        regs: list[object] = regs_raw if isinstance(regs_raw, list) else []
        register_count = len(regs)
        return {"register_count": register_count, "top_keys": keys}
    return {"register_count": 0, "top_keys": []}


def _extract_enum_sets(text: str, path_str: str) -> list[dict]:
    enum_sets: list[dict] = []
    for enum_match in _ENUM_RE.finditer(text):
        body = enum_match.group(1)
        enum_type = enum_match.group(2)
        states: list[str] = []
        for token in body.split(","):
            candidate = token.strip()
            if not candidate:
                continue
            state_name = candidate.split("=")[0].strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", state_name):
                states.append(state_name)
        if states:
            deduped = sorted(set(states))
            enum_sets.append(
                {
                    "enum_type": enum_type,
                    "states": deduped,
                    "state_count": len(deduped),
                    "file": path_str,
                }
            )
    return enum_sets


def _extract_fsm_candidates(text: str, path_str: str) -> list[dict]:
    fsm_candidates: list[dict] = []
    for case_match in _CASE_RE.finditer(text):
        state_expr = case_match.group(1)
        body = case_match.group(2)
        case_states = sorted(set(_CASE_LABEL_RE.findall(body)))

        next_states: set[str] = set()
        for lhs, rhs in _NEXT_ASSIGN_RE.findall(body):
            if "state" not in lhs.lower():
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", rhs):
                next_states.add(rhs)

        fsm_candidates.append(
            {
                "state_expression": state_expr,
                "states": case_states,
                "state_count": len(case_states),
                "next_state_values": sorted(next_states),
                "file": path_str,
            }
        )
    return fsm_candidates


def _extract_instantiated_modules(text: str, module_set: set[str]) -> set[str]:
    instantiated: set[str] = set()
    # Matches:
    #   some_module u_some_instance (
    #   some_module #( ... ) u_some_instance (
    inst_re = re.compile(
        r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:#\s*\([\s\S]*?\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        flags=re.MULTILINE,
    )
    for match in inst_re.finditer(text):
        mod_name = match.group(1)
        if mod_name in module_set:
            instantiated.add(mod_name)
    return instantiated


def analyze(rtl_path: Path, spec_path: Path, csr_map_path: Path) -> dict:
    rtl_files = discover_rtl_files(rtl_path)
    rtl_texts = {str(p): read_text(p, max_chars=500_000) for p in rtl_files}
    spec_text = read_text(spec_path)
    csr_summary = _parse_csr_map(csr_map_path)

    module_names: list[str] = []
    ports: list[dict] = []
    total_lines = 0
    enum_state_sets: list[dict] = []
    fsm_candidates: list[dict] = []

    for path_str, text in rtl_texts.items():
        total_lines += text.count("\n") + 1
        module_names.extend(_MODULE_RE.findall(text))
        enum_state_sets.extend(_extract_enum_sets(text=text, path_str=path_str))
        fsm_candidates.extend(_extract_fsm_candidates(text=text, path_str=path_str))

        for match in _PORT_RE.finditer(text):
            ports.append(
                {
                    "direction": match.group(1),
                    "width": (match.group(2) or "").strip(),
                    "name": match.group(3),
                    "file": path_str,
                }
            )

    port_names = [p["name"] for p in ports]
    tlul_ports = sorted([n for n in port_names if n.startswith("tl_")])

    protocol_hints = []
    for proto in ("uart", "spi", "i2c", "gpio", "hmac", "aes", "timer"):
        if any(proto in n.lower() for n in port_names):
            protocol_hints.append(proto)

    interface_hints = {
        "interrupt_candidates": sorted(
            {n for n in port_names if ("intr" in n.lower() or "irq" in n.lower())}
        ),
        "alert_candidates": sorted({n for n in port_names if "alert" in n.lower()}),
    }

    clock_candidates = [n for n in port_names if "clk" in n.lower()]
    reset_candidates = [n for n in port_names if "rst" in n.lower()]

    module_set = set(module_names)
    instantiated_modules: set[str] = set()
    for text in rtl_texts.values():
        instantiated_modules.update(
            _extract_instantiated_modules(text=text, module_set=module_set)
        )

    unique_modules = sorted(module_set)
    top_modules = sorted([m for m in unique_modules if m not in instantiated_modules])
    selected_top = (
        top_modules[0] if top_modules else (unique_modules[0] if unique_modules else "")
    )

    for proto in ("uart", "spi", "i2c", "gpio", "hmac", "aes", "timer"):
        if proto in " ".join(unique_modules).lower() or proto in spec_text.lower():
            protocol_hints.append(proto)

    deduped_protocol_hints = sorted(set(protocol_hints))

    return {
        "rtl_files": [str(p) for p in rtl_files],
        "total_rtl_lines": total_lines,
        "modules": unique_modules,
        "top_modules": top_modules,
        "selected_top": selected_top,
        "port_count": len(ports),
        "ports": ports[:200],
        "tlul_detected": len(tlul_ports) > 0,
        "tlul_ports": tlul_ports,
        "protocol_hints": deduped_protocol_hints,
        "clock_candidates": clock_candidates,
        "reset_candidates": reset_candidates,
        "interface_hints": interface_hints,
        "enum_state_sets": enum_state_sets[:40],
        "fsm_candidates": fsm_candidates[:40],
        "estimated_fsm_blocks": len(fsm_candidates),
        "csr_summary": csr_summary,
        "spec_excerpt": spec_text[:4000],
    }
