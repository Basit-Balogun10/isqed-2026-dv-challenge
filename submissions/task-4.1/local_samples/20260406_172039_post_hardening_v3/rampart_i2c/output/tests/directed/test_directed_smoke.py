from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

THIS_DIR = Path(__file__).resolve().parent
TB_ROOT = THIS_DIR.parent.parent / "testbench"
if str(TB_ROOT) not in sys.path:
    sys.path.insert(0, str(TB_ROOT))

if str(THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(THIS_DIR.parent))

from agents.tl_ul_agent import TlUlDriver
from coverage.coverage import CoverageCollector
from env import VerificationEnv


REG_ADDRS = [0x0, 0x4, 0x8, 0xC, 0x10, 0x14, 0x18, 0x1C]


def _record_func_cov(tag: str, counters: dict) -> None:
    out_file = os.getenv("AUTOVERIFIER_FUNC_COV_FILE", "").strip()
    if not out_file:
        return
    cov_path = Path(out_file)
    cov_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {}
    if cov_path.exists():
        try:
            payload = json.loads(cov_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    payload[tag] = counters
    cov_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@cocotb.test()
async def test_directed_csr_smoke(dut):
    """Directed smoke test: reset, deterministic writes, deterministic reads."""
    clk = getattr(dut, "clk_i")
    cocotb.start_soon(Clock(clk, 2, unit="step").start())

    env = VerificationEnv(dut)
    driver = env.tl_driver
    coverage = CoverageCollector()
    successful_ops = 0

    await driver.apply_reset(cycles=8)
    coverage.hit("reset_sequence")

    for idx, addr in enumerate(REG_ADDRS):
        data = (0xA5A50000 + idx) & 0xFFFFFFFF
        wr = await driver.csr_write(addr=addr, data=data)
        coverage.hit_operation(op="write", addr=addr, data=data, error=bool(int(wr.get("error", 0))))
        if int(wr.get("error", 0)) == 0:
            successful_ops += 1

        rd = await driver.csr_read(addr=addr)
        coverage.hit_operation(op="read", addr=addr, error=bool(int(rd.get("error", 0))))
        if int(rd.get("error", 0)) == 0:
            successful_ops += 1

    await RisingEdge(clk)
    assert successful_ops > 0, "No successful TL-UL operations observed in directed smoke test"
    _record_func_cov("test_directed_csr_smoke", coverage.snapshot())


@cocotb.test()
async def test_directed_error_probe(dut):
    """Directed boundary/error probe on out-of-range-like addresses."""
    clk = getattr(dut, "clk_i")
    cocotb.start_soon(Clock(clk, 2, unit="step").start())

    env = VerificationEnv(dut)
    driver = env.tl_driver
    coverage = CoverageCollector()
    await driver.apply_reset(cycles=4)

    random.seed(41)
    for _ in range(4):
        addr = random.choice([0x3FC, 0x7FC, 0xFFC])
        rd = await driver.csr_read(addr=addr)
        coverage.hit_operation(op="read", addr=addr, error=bool(int(rd.get("error", 0))))
    await RisingEdge(clk)
    _record_func_cov("test_directed_error_probe", coverage.snapshot())
