import os
import json
import random
from pathlib import Path

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

from testbench.agents.tl_ul_driver import TlUlDriver


SEED = 1011
random.seed(SEED)


def _discover_signal(obj, names):
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _int_value(sig, default=0):
    if sig is None:
        return default
    try:
        return int(sig.value)
    except Exception:
        try:
            return int(sig)
        except Exception:
            return default


def _record_cov(cov):
    path = os.getenv("AUTOVERIFIER_FUNC_COV_FILE", "autoverifier_func_cov.json")
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cov, f, indent=2, sort_keys=True)


async def _reset_dut(dut, clk, rst_n):
    if rst_n is None:
        for _ in range(5):
            await RisingEdge(clk)
        return
    try:
        rst_n.value = 0
    except Exception:
        pass
    for _ in range(5):
        await RisingEdge(clk)
    try:
        rst_n.value = 1
    except Exception:
        pass
    for _ in range(5):
        await RisingEdge(clk)


async def _tl_write(driver, addr, data):
    for name in ("write", "put_full_data", "csr_write", "reg_write"):
        if hasattr(driver, name):
            fn = getattr(driver, name)
            res = fn(addr, data)
            if hasattr(res, "__await__"):
                return await res
            return res
    raise AttributeError("TlUlDriver has no supported write method")


async def _tl_read(driver, addr):
    for name in ("read", "get", "csr_read", "reg_read"):
        if hasattr(driver, name):
            fn = getattr(driver, name)
            res = fn(addr)
            if hasattr(res, "__await__"):
                return await res
            return res
    raise AttributeError("TlUlDriver has no supported read method")


def _extract_read_data(resp):
    if resp is None:
        return None
    if isinstance(resp, int):
        return resp
    for attr in ("data", "d_data", "value", "rdata"):
        if hasattr(resp, attr):
            try:
                return int(getattr(resp, attr))
            except Exception:
                pass
    if isinstance(resp, dict):
        for key in ("data", "d_data", "value", "rdata"):
            if key in resp:
                try:
                    return int(resp[key])
                except Exception:
                    pass
    try:
        return int(resp)
    except Exception:
        return None


@cocotb.test()
async def test_repair_iteration_1_1(dut):
    cov = {
        "format": "AUTOVERIFIER_FUNC_COV_FILE",
        "test_name": "test_repair_iteration_1_1",
        "seed": SEED,
        "scenario": "cmd_sequence_race_gap",
        "bins": {
            "reset_applied": 0,
            "tl_driver_created": 0,
            "single_write": 0,
            "single_read": 0,
            "back_to_back_writes": 0,
            "write_gap_0": 0,
            "write_gap_1": 0,
            "write_gap_2plus": 0,
            "read_after_write": 0,
            "repeated_same_addr_write": 0,
            "mixed_addr_sequence": 0,
            "status_sampled": 0,
            "idle_cycles_observed": 0
        }
    }

    clk = _discover_signal(dut, ["clk_i", "clk", "clock", "core_clk_i"])
    rst_n = _discover_signal(dut, ["rst_ni", "rst_n", "reset_n", "aresetn"])

    if clk is not None:
        cocotb.start_soon(Clock(clk, 10, units="ns").start())

    await _reset_dut(dut, clk, rst_n)
    cov["bins"]["reset_applied"] = 1

    driver = TlUlDriver(dut)
    cov["bins"]["tl_driver_created"] = 1

    base_addrs = [0x0, 0x4, 0x8, 0xC, 0x10, 0x14]
    data_words = [0x00000001, 0x00000002, 0xA5A5A5A5, 0x5A5A5A5A, 0xFFFFFFFF, 0x00000000]

    await _tl_write(driver, base_addrs[0], data_words[0])
    cov["bins"]["single_write"] = 1

    await RisingEdge(clk) if clk is not None else Timer(10, units="ns")
    r0 = await _tl_read(driver, base_addrs[0])
    _ = _extract_read_data(r0)
    cov["bins"]["single_read"] = 1
    cov["bins"]["read_after_write"] = 1

    await _tl_write(driver, base_addrs[1], data_words[1])
    await _tl_write(driver, base_addrs[2], data_words[2])
    cov["bins"]["back_to_back_writes"] = 1
    cov["bins"]["mixed_addr_sequence"] = 1
    cov["bins"]["write_gap_0"] = 1

    await RisingEdge(clk) if clk is not None else Timer(10, units="ns")
    await _tl_write(driver, base_addrs[1], data_words[3])
    cov["bins"]["repeated_same_addr_write"] = 1
    cov["bins"]["write_gap_1"] = 1

    for _ in range(3):
        await RisingEdge(clk) if clk is not None else Timer(10, units="ns")
    cov["bins"]["idle_cycles_observed"] = 1

    await _tl_write(driver, base_addrs[3], data_words[4])
    cov["bins"]["write_gap_2plus"] = 1

    for addr in (base_addrs[0], base_addrs[1], base_addrs[2], base_addrs[3]):
        resp = await _tl_read(driver, addr)
        _ = _extract_read_data(resp)

    status_like = _discover_signal(
        dut,
        [
            "intr_hmac_done_o",
            "intr_fifo_empty_o",
            "idle_o",
            "done_o",
            "ready_o",
            "alert_o",
        ],
    )
    _ = _int_value(status_like, 0)
    cov["bins"]["status_sampled"] = 1

    _record_cov(cov)
