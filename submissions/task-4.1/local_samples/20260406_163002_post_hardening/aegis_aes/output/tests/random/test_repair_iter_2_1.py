import os
import json
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly

from testbench.agents import TlUlDriver


SEED = 0xA5E17
random.seed(SEED)


def _get_signal(dut, names):
    for name in names:
        if hasattr(dut, name):
            return getattr(dut, name)
    raise AttributeError(f"None of the candidate signals exist: {names}")


def _sig_int(sig):
    try:
        return int(sig.value)
    except Exception:
        return int(sig)


def _write_cov(cov):
    path = os.getenv("AUTOVERIFIER_FUNC_COV_FILE")
    if not path:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if p.exists():
        try:
            data = json.loads(p.read_text())
        except Exception:
            data = {}
    data.setdefault("functional_coverage", {})
    data["functional_coverage"].update(cov)
    p.write_text(json.dumps(data, indent=2, sort_keys=True))


async def _wait_cycles(clk, n):
    for _ in range(n):
        await RisingEdge(clk)


async def _reset_dut(dut, clk, rst_n):
    rst_n.value = 0
    await _wait_cycles(clk, 5)
    rst_n.value = 1
    await _wait_cycles(clk, 2)


async def _tl_write(driver, addr, data, mask=0xF):
    await driver.write(addr, data, mask)


async def _tl_read(driver, addr):
    return await driver.read(addr)


@cocotb.test()
async def test_repair_iteration_2_1(dut):
    clk = _get_signal(dut, ["clk_i"])
    rst_n = _get_signal(dut, ["rst_ni"])

    cocotb.start_soon(Clock(clk, 10, units="ns").start())
    await _reset_dut(dut, clk, rst_n)

    driver = TlUlDriver(dut, "tl_i", clk, rst_n)
    await driver.reset()

    cov = {
        "seed": SEED,
        "scenario": "key_schedule_state_reuse_gap",
        "ops": {
            "key_programmed": 0,
            "iv_programmed": 0,
            "data_programmed": 0,
            "start_seen": 0,
            "done_seen": 0,
            "back_to_back_start": 0,
            "status_polled": 0,
        },
        "observations": {
            "done_high": 0,
            "input_ready_high": 0,
            "output_valid_high": 0,
        },
    }

    base = 0x0
    key_words = [0x00112233, 0x44556677, 0x8899AABB, 0xCCDDEEFF]
    iv_words = [0x0F1E2D3C, 0x4B5A6978, 0x8796A5B4, 0xC3D2E1F0]
    pt_words_1 = [0x6BC1BEE2, 0x2E409F96, 0xE93D7E11, 0x7393172A]
    pt_words_2 = [0xAE2D8A57, 0x1E03AC9C, 0x9EB76FAC, 0x45AF8E51]

    for i, w in enumerate(key_words):
        await _tl_write(driver, base + 0x10 + 4 * i, w)
        cov["ops"]["key_programmed"] += 1

    for i, w in enumerate(iv_words):
        await _tl_write(driver, base + 0x20 + 4 * i, w)
        cov["ops"]["iv_programmed"] += 1

    for i, w in enumerate(pt_words_1):
        await _tl_write(driver, base + 0x30 + 4 * i, w)
        cov["ops"]["data_programmed"] += 1

    await _tl_write(driver, base + 0x00, 0x1)
    cov["ops"]["start_seen"] += 1

    for _ in range(200):
        await RisingEdge(clk)
        await ReadOnly()
        if hasattr(dut, "done_o") and _sig_int(dut.done_o):
            cov["observations"]["done_high"] = 1
            cov["ops"]["done_seen"] += 1
            break
        if hasattr(dut, "input_ready_o") and _sig_int(dut.input_ready_o):
            cov["observations"]["input_ready_high"] = 1
        if hasattr(dut, "output_valid_o") and _sig_int(dut.output_valid_o):
            cov["observations"]["output_valid_high"] = 1
        cov["ops"]["status_polled"] += 1

    for i, w in enumerate(pt_words_2):
        await _tl_write(driver, base + 0x30 + 4 * i, w)
        cov["ops"]["data_programmed"] += 1

    await _tl_write(driver, base + 0x00, 0x1)
    cov["ops"]["start_seen"] += 1
    cov["ops"]["back_to_back_start"] += 1

    for _ in range(200):
        await RisingEdge(clk)
        await ReadOnly()
        if hasattr(dut, "done_o") and _sig_int(dut.done_o):
            cov["observations"]["done_high"] = 1
            cov["ops"]["done_seen"] += 1
            break
        if hasattr(dut, "input_ready_o") and _sig_int(dut.input_ready_o):
            cov["observations"]["input_ready_high"] = 1
        if hasattr(dut, "output_valid_o") and _sig_int(dut.output_valid_o):
            cov["observations"]["output_valid_high"] = 1
        cov["ops"]["status_polled"] += 1

    for _ in range(20):
        await RisingEdge(clk)
        await ReadOnly()
        if hasattr(dut, "done_o") and _sig_int(dut.done_o):
            cov["observations"]["done_high"] = 1
        if hasattr(dut, "input_ready_o") and _sig_int(dut.input_ready_o):
            cov["observations"]["input_ready_high"] = 1
        if hasattr(dut, "output_valid_o") and _sig_int(dut.output_valid_o):
            cov["observations"]["output_valid_high"] = 1

    _write_cov(cov)
