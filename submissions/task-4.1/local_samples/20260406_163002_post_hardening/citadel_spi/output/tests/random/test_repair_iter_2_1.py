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
        return int(os.getenv(name, default))
    except Exception:
        return default


def _get_env_path(name, default):
    return Path(os.getenv(name, default))


class _FuncCov:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {
            "schema": "AUTOVERIFIER_FUNC_COV_FILE",
            "version": 1,
            "bins": {},
        }

    def hit(self, name):
        self.data["bins"][name] = int(self.data["bins"].get(name, 0)) + 1

    def write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, sort_keys=True)


async def _wait_cycles(clk, n):
    for _ in range(n):
        await RisingEdge(clk)


async def _reset_dut(dut):
    dut.rst_ni.value = 0
    await _wait_cycles(dut.clk_i, 5)
    dut.rst_ni.value = 1
    await _wait_cycles(dut.clk_i, 5)


async def _safe_write(driver, addr, data, mask=None):
    if mask is None:
        mask = 0xF
    await driver.write(addr, data, mask)


async def _safe_read(driver, addr):
    return await driver.read(addr)


@cocotb.test()
async def test_repair_iteration_2_1(dut):
    seed = _get_env_int("AUTOVERIFIER_SEED", 12345)
    random.seed(seed)

    cov_file = _get_env_path("AUTOVERIFIER_FUNC_COV_FILE", "autoverifier_func_cov.json")
    fcov = _FuncCov(cov_file)

    if hasattr(dut, "clk_i"):
        cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())

    await _reset_dut(dut)
    fcov.hit("reset_released")

    driver = TlUlDriver(dut, "tl")
    await driver.start()

    base_addrs = [0x00, 0x04, 0x08, 0x0C]
    patterns = [0x00000000, 0xFFFFFFFF, 0xA5A5A5A5, 0x5A5A5A5A]

    for i, addr in enumerate(base_addrs):
        data = patterns[i]
        await _safe_write(driver, addr, data)
        fcov.hit(f"write_addr_{i}")

    for i, addr in enumerate(base_addrs):
        _ = await _safe_read(driver, addr)
        fcov.hit(f"read_addr_{i}")

    for _ in range(8):
        addr = random.choice(base_addrs)
        data = random.getrandbits(32)
        await _safe_write(driver, addr, data)
        fcov.hit("random_write")

    for _ in range(8):
        addr = random.choice(base_addrs)
        _ = await _safe_read(driver, addr)
        fcov.hit("random_read")

    if hasattr(dut, "sclk_o"):
        await ReadOnly()
        _ = int(dut.sclk_o.value)
        fcov.hit("sclk_observed")

    if hasattr(dut, "cs_o"):
        await ReadOnly()
        _ = int(dut.cs_o.value)
        fcov.hit("cs_observed")

    await _wait_cycles(dut.clk_i, 10)
    fcov.hit("test_complete")

    fcov.write()
