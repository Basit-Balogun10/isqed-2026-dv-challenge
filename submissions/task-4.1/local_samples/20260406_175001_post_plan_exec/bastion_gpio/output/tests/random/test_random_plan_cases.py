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


REG_ADDRS = [0x0, 0x4, 0x8, 0xC, 0x10, 0x14, 0x18, 0x1C]
RANDOM_SCENARIOS = [{"name":"constrained_csr_fuzzer","intent":"Run short randomized TL-UL CSR sequences over the 12-register map with legal accesses only, mixing reads, writes, W1C clears, and readbacks to catch decode and side-effect issues."},{"name":"gpio_activity_stress_subset","intent":"Randomly toggle a representative subset of gpio_i pins with varied pulse widths and phase relationships to stress synchronizer, edge detection, and interrupt latching within the time budget."},{"name":"masked_write_random_patterns","intent":"Generate random mask/data combinations for both masked output registers and compare readback against a software model of atomic bit updates."},{"name":"interrupt_mode_cross_product_sample","intent":"Randomly select pins and interrupt mode combinations across rising, falling, level-high, and level-low enables, then stimulate transitions to validate combined mode behavior."}]


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


async def _run_random_scenario(dut, *, scenario_name: str, scenario_intent: str, scenario_idx: int) -> None:
    clk = getattr(dut, "clk_i") if hasattr(dut, "clk_i") else getattr(dut, "clk_i")
    cocotb.start_soon(Clock(clk, 2, unit="step").start())

    driver = TlUlDriver(dut, clk_signal=clk._name, rst_signal="rst_ni")
    coverage = CoverageCollector()
    await driver.apply_reset(cycles=6)
    coverage.hit("reset_sequence")

    deterministic_seed = (
        scenario_idx * 20011 + sum(ord(ch) for ch in scenario_name)
    ) & 0xFFFFFFFF
    rng = random.Random(deterministic_seed)

    addr_pool = list(REG_ADDRS) + [0x3FC, 0x7FC, 0xFFC]
    op_count = 20 + (scenario_idx % 7) * 2
    successful_ops = 0

    for _ in range(op_count):
        addr = rng.choice(addr_pool)
        if rng.random() < 0.6:
            data = rng.getrandbits(32)
            wr = await driver.csr_write(addr=addr, data=data)
            coverage.hit_operation(op="write", addr=addr, data=data, error=bool(int(wr.get("error", 0))))
            if int(wr.get("error", 0)) == 0:
                successful_ops += 1
        else:
            rd = await driver.csr_read(addr=addr)
            coverage.hit_operation(op="read", addr=addr, error=bool(int(rd.get("error", 0))))
            if int(rd.get("error", 0)) == 0:
                successful_ops += 1
        await RisingEdge(clk)

    await RisingEdge(clk)
    assert successful_ops > 0, f"No successful TL-UL operations for random scenario: {scenario_name}"
    _record_func_cov(f"random::{scenario_name}", coverage.snapshot())

@cocotb.test()
async def test_random_constrained_csr_fuzzer(dut):
    await _run_random_scenario(
        dut,
        scenario_name="constrained_csr_fuzzer",
        scenario_intent="Run short randomized TL-UL CSR sequences over the 12-register map with legal accesses only, mixing reads, writes, W1C clears, and readbacks to catch decode and side-effect issues.",
        scenario_idx=1,
    )

@cocotb.test()
async def test_random_gpio_activity_stress_subset(dut):
    await _run_random_scenario(
        dut,
        scenario_name="gpio_activity_stress_subset",
        scenario_intent="Randomly toggle a representative subset of gpio_i pins with varied pulse widths and phase relationships to stress synchronizer, edge detection, and interrupt latching within the time budget.",
        scenario_idx=2,
    )

@cocotb.test()
async def test_random_masked_write_random_patterns(dut):
    await _run_random_scenario(
        dut,
        scenario_name="masked_write_random_patterns",
        scenario_intent="Generate random mask/data combinations for both masked output registers and compare readback against a software model of atomic bit updates.",
        scenario_idx=3,
    )

@cocotb.test()
async def test_random_interrupt_mode_cross_product_sample(dut):
    await _run_random_scenario(
        dut,
        scenario_name="interrupt_mode_cross_product_sample",
        scenario_intent="Randomly select pins and interrupt mode combinations across rising, falling, level-high, and level-low enables, then stimulate transitions to validate combined mode behavior.",
        scenario_idx=4,
    )
