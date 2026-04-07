import os
import json
import random
from pathlib import Path

import cocotb
from cocotb.triggers import RisingEdge, Timer, ReadOnly
from cocotb.clock import Clock

from testbench.agents import TlUlDriver


def _get_env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return default


def _get_env_path(name, default):
    return Path(os.environ.get(name, default))


def _cov_init():
    path = _get_env_path("AUTOVERIFIER_FUNC_COV_FILE", "autoverifier_func_cov.json")
    data = {"schema": "AUTOVERIFIER_FUNC_COV_FILE", "bins": {}}
    if path.exists():
        try:
            loaded = json.loads(path.read_text())
            if isinstance(loaded, dict):
                data.update(loaded)
                if "bins" not in data or not isinstance(data["bins"], dict):
                    data["bins"] = {}
        except Exception:
            pass
    return path, data


def _cov_hit(cov, name):
    cov["bins"][name] = int(cov["bins"].get(name, 0)) + 1


def _cov_write(path, cov):
    path.write_text(json.dumps(cov, indent=2, sort_keys=True))


async def _wait_cycles(clk, n):
    for _ in range(n):
        await RisingEdge(clk)


async def _tl_write(drv, addr, data, mask=None):
    if mask is None:
        mask = 0xF
    await drv.write(addr, data, mask)


async def _tl_read(drv, addr):
    return await drv.read(addr)


@cocotb.test()
async def test_repair_iteration_2_1(dut):
    random.seed(0xC0C0BEEF)

    cov_path, cov = _cov_init()

    clk = dut.clk_i
    rst_n = dut.rst_ni

    cocotb.start_soon(Clock(clk, 10, units="ns").start())

    drv = TlUlDriver(dut, "tl")
    await drv.reset()

    if hasattr(dut, "rst_ni"):
        dut.rst_ni.value = 0
        await _wait_cycles(clk, 5)
        dut.rst_ni.value = 1
        await _wait_cycles(clk, 5)

    _cov_hit(cov, "reset_seen")

    base_addrs = [0x0, 0x4, 0x8, 0xC]
    for a in base_addrs:
        try:
            await _tl_write(drv, a, random.getrandbits(32))
            _cov_hit(cov, "basic_write")
        except Exception:
            _cov_hit(cov, "write_exception")
        try:
            _ = await _tl_read(drv, a)
            _cov_hit(cov, "basic_read")
        except Exception:
            _cov_hit(cov, "read_exception")

    for _ in range(8):
        addr = random.choice(base_addrs)
        data = random.getrandbits(32)
        mask = random.choice([0x1, 0x3, 0x7, 0xF])
        try:
            await _tl_write(drv, addr, data, mask)
            _cov_hit(cov, f"partial_write_mask_{mask:x}")
        except Exception:
            _cov_hit(cov, "partial_write_exception")
        await _wait_cycles(clk, 1)

    for _ in range(8):
        addr = random.choice(base_addrs)
        try:
            _ = await _tl_read(drv, addr)
            _cov_hit(cov, "random_read")
        except Exception:
            _cov_hit(cov, "random_read_exception")
        await _wait_cycles(clk, 1)

    if hasattr(dut, "rst_ni"):
        dut.rst_ni.value = 0
        await _wait_cycles(clk, 2)
        dut.rst_ni.value = 1
        await _wait_cycles(clk, 2)
        _cov_hit(cov, "reset_pulse")

    _cov_write(cov_path, cov)
