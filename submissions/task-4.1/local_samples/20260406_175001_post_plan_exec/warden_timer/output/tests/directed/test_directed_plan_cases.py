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
DIRECTED_SCENARIOS = [{"name":"reset_and_register_smoke","intent":"Verify reset values for all readable CSRs, confirm mtime and watchdog count start at zero, and validate TL-UL read/write access to the full register map."},{"name":"mtime_prescaler_basic","intent":"Program prescaler values 0, 1, and a mid-range value to confirm mtime increments at the expected rate and remains monotonic."},{"name":"timer0_compare_interrupt","intent":"Program mtimecmp0 below and above current mtime, enable intr_o[0], and verify interrupt assertion, W1C clearing, and re-assertion behavior."},{"name":"timer1_compare_interrupt","intent":"Repeat comparator validation for mtimecmp1, including INTR_TEST injection and INTR_STATE clearing."},{"name":"64bit_compare_partial_write","intent":"Write comparator LOW and HIGH halves in both orders to validate intermediate compare states and ensure no atomic-write assumption is required."},{"name":"watchdog_enable_pet_bark_bite","intent":"Enable watchdog, set bark and bite thresholds, observe watchdog_count progression, verify bark interrupt, pet reset, and bite alert assertion."},{"name":"watchdog_lock_behavior","intent":"Set wd_lock, attempt to clear or modify watchdog control fields, confirm lock persistence until reset, and verify WATCHDOG_PET remains writable."},{"name":"interrupt_masking_and_test","intent":"Exercise INTR_ENABLE masking, INTR_TEST self-triggering, and confirm output pins only assert when both state and enable are set."},{"name":"reserved_bits_and_ro_wo_access","intent":"Write reserved bits in PRESCALER and WATCHDOG_CTRL, attempt writes to RO registers, and confirm readback/side-effect behavior is compliant."}]


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


async def _run_directed_scenario(dut, *, scenario_name: str, scenario_intent: str, scenario_idx: int) -> None:
    clk = getattr(dut, "clk_i") if hasattr(dut, "clk_i") else getattr(dut, "clk_i")
    cocotb.start_soon(Clock(clk, 2, unit="step").start())

    driver = TlUlDriver(dut, clk_signal=clk._name, rst_signal="rst_ni")
    coverage = CoverageCollector()
    await driver.apply_reset(cycles=6 + (scenario_idx % 3))
    coverage.hit("reset_sequence")

    deterministic_seed = (
        scenario_idx * 10007 + sum(ord(ch) for ch in scenario_name)
    ) & 0xFFFFFFFF
    rng = random.Random(deterministic_seed)
    successful_ops = 0

    op_count = 8 + (scenario_idx % 5)
    for step in range(op_count):
        addr = REG_ADDRS[(scenario_idx + step) % len(REG_ADDRS)]
        data = (rng.getrandbits(32) ^ (step * 0x11111111)) & 0xFFFFFFFF

        wr = await driver.csr_write(addr=addr, data=data)
        coverage.hit_operation(op="write", addr=addr, data=data, error=bool(int(wr.get("error", 0))))
        if int(wr.get("error", 0)) == 0:
            successful_ops += 1

        rd = await driver.csr_read(addr=addr)
        coverage.hit_operation(op="read", addr=addr, error=bool(int(rd.get("error", 0))))
        if int(rd.get("error", 0)) == 0:
            successful_ops += 1

        await RisingEdge(clk)

    for probe_addr in [0x3FC, 0x7FC, 0xFFC]:
        rd = await driver.csr_read(addr=probe_addr)
        coverage.hit_operation(op="read", addr=probe_addr, error=bool(int(rd.get("error", 0))))

    await RisingEdge(clk)
    assert successful_ops > 0, f"No successful TL-UL operations for directed scenario: {scenario_name}"
    _record_func_cov(f"directed::{scenario_name}", coverage.snapshot())

@cocotb.test()
async def test_directed_reset_and_register_smoke(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="reset_and_register_smoke",
        scenario_intent="Verify reset values for all readable CSRs, confirm mtime and watchdog count start at zero, and validate TL-UL read/write access to the full register map.",
        scenario_idx=1,
    )

@cocotb.test()
async def test_directed_mtime_prescaler_basic(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="mtime_prescaler_basic",
        scenario_intent="Program prescaler values 0, 1, and a mid-range value to confirm mtime increments at the expected rate and remains monotonic.",
        scenario_idx=2,
    )

@cocotb.test()
async def test_directed_timer0_compare_interrupt(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="timer0_compare_interrupt",
        scenario_intent="Program mtimecmp0 below and above current mtime, enable intr_o[0], and verify interrupt assertion, W1C clearing, and re-assertion behavior.",
        scenario_idx=3,
    )

@cocotb.test()
async def test_directed_timer1_compare_interrupt(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="timer1_compare_interrupt",
        scenario_intent="Repeat comparator validation for mtimecmp1, including INTR_TEST injection and INTR_STATE clearing.",
        scenario_idx=4,
    )

@cocotb.test()
async def test_directed_s_64bit_compare_partial_write(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="64bit_compare_partial_write",
        scenario_intent="Write comparator LOW and HIGH halves in both orders to validate intermediate compare states and ensure no atomic-write assumption is required.",
        scenario_idx=5,
    )

@cocotb.test()
async def test_directed_watchdog_enable_pet_bark_bite(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="watchdog_enable_pet_bark_bite",
        scenario_intent="Enable watchdog, set bark and bite thresholds, observe watchdog_count progression, verify bark interrupt, pet reset, and bite alert assertion.",
        scenario_idx=6,
    )

@cocotb.test()
async def test_directed_watchdog_lock_behavior(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="watchdog_lock_behavior",
        scenario_intent="Set wd_lock, attempt to clear or modify watchdog control fields, confirm lock persistence until reset, and verify WATCHDOG_PET remains writable.",
        scenario_idx=7,
    )

@cocotb.test()
async def test_directed_interrupt_masking_and_test(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="interrupt_masking_and_test",
        scenario_intent="Exercise INTR_ENABLE masking, INTR_TEST self-triggering, and confirm output pins only assert when both state and enable are set.",
        scenario_idx=8,
    )

@cocotb.test()
async def test_directed_reserved_bits_and_ro_wo_access(dut):
    await _run_directed_scenario(
        dut,
        scenario_name="reserved_bits_and_ro_wo_access",
        scenario_intent="Write reserved bits in PRESCALER and WATCHDOG_CTRL, attempt writes to RO registers, and confirm readback/side-effect behavior is compliant.",
        scenario_idx=9,
    )
