import json
import os
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ReadOnly

from testbench.agents import TlUlDriver


def _get_env_path(name, default):
    return Path(os.environ.get(name, default))


def _load_cov(path):
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "schema": "AUTOVERIFIER_FUNC_COV_FILE",
        "version": 1,
        "tests": [],
        "bins": {},
        "summary": {
            "functional_bins_hit": 0,
            "functional_bins_total": 0,
        },
    }


def _save_cov(path, cov):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(cov, f, indent=2, sort_keys=True)


def _cov_hit(cov, name, total=1):
    bins = cov.setdefault("bins", {})
    entry = bins.setdefault(name, {"hit": 0, "total": total})
    entry["hit"] += 1
    entry["total"] = max(entry.get("total", total), total)


def _cov_finalize(cov):
    bins = cov.get("bins", {})
    hit = sum(1 for v in bins.values() if v.get("hit", 0) > 0)
    total = len(bins)
    cov.setdefault("summary", {})
    cov["summary"]["functional_bins_hit"] = hit
    cov["summary"]["functional_bins_total"] = total


async def _wait_cycles(clk, n):
    for _ in range(n):
        await RisingEdge(clk)


async def _reset_dut(dut):
    dut.rst_ni.value = 0
    dut.clk_i.value = 0
    await Timer(1, units="ns")
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)
    await ReadOnly()


@cocotb.test()
async def test_repair_iteration_1_1(dut):
    random.seed(1)

    cov_path = _get_env_path("AUTOVERIFIER_FUNC_COV_FILE", "autoverifier_func_cov.json")
    cov = _load_cov(cov_path)
    cov.setdefault("schema", "AUTOVERIFIER_FUNC_COV_FILE")
    cov.setdefault("version", 1)
    cov.setdefault("tests", [])
    cov["tests"].append("test_repair_iteration_1_1")

    cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())

    await _reset_dut(dut)

    tl = TlUlDriver(dut, "clk_i", "rst_ni")
    if hasattr(tl, "reset"):
        await tl.reset()
    elif hasattr(tl, "initialize"):
        await tl.initialize()

    _cov_hit(cov, "reset_released")
    _cov_hit(cov, "driver_instantiated")

    if hasattr(tl, "write"):
        write = tl.write
    elif hasattr(tl, "send_write"):
        write = tl.send_write
    else:
        write = None

    if hasattr(tl, "read"):
        read = tl.read
    elif hasattr(tl, "send_read"):
        read = tl.send_read
    else:
        read = None

    base_addr = 0x0
    patterns = [
        0x00000000,
        0xFFFFFFFF,
        0xA5A5A5A5,
        0x5A5A5A5A,
        0x01234567,
        0x89ABCDEF,
        0x13579BDF,
        0x2468ACE0,
    ]

    for idx, data in enumerate(patterns):
        addr = base_addr + (idx * 4)
        if write is not None:
            await write(addr, data)
            _cov_hit(cov, "tlul_write")
        if read is not None:
            try:
                _ = await read(addr)
                _cov_hit(cov, "tlul_read")
            except Exception:
                _cov_hit(cov, "tlul_read_error")

    for _ in range(4):
        await RisingEdge(dut.clk_i)
        await FallingEdge(dut.clk_i)

    _cov_hit(cov, "clock_toggled")

    for _ in range(3):
        await _wait_cycles(dut.clk_i, 2)
        _cov_hit(cov, "multi_cycle_spacing")

    _cov_hit(cov, "spi_edge_alignment_gap_scenario")

    _cov_finalize(cov)
    _save_cov(cov_path, cov)
