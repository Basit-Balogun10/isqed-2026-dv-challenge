import os
import json
import random
from pathlib import Path

import cocotb
from cocotb.triggers import RisingEdge, Timer, ReadOnly
from cocotb.clock import Clock

from testbench.agents import TlUlDriver


class FunctionalCoverage:
    def __init__(self):
        self.bins = {}
        self.total_bins = 0

    def add_bin(self, name):
        if name not in self.bins:
            self.bins[name] = 0
            self.total_bins += 1

    def hit(self, name):
        self.add_bin(name)
        self.bins[name] += 1

    def write_json(self, path):
        data = {
            "schema": "AUTOVERIFIER_FUNC_COV_FILE",
            "version": 1,
            "bins": [{"name": k, "hits": v} for k, v in sorted(self.bins.items())],
            "summary": {
                "bins_hit": sum(1 for v in self.bins.values() if v > 0),
                "bins_total": self.total_bins,
            },
        }
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))


async def wait_cycles(clk, n):
    for _ in range(n):
        await RisingEdge(clk)


async def reset_dut(dut, cycles=5):
    dut.rst_ni.value = 0
    await wait_cycles(dut.clk_i, cycles)
    dut.rst_ni.value = 1
    await wait_cycles(dut.clk_i, cycles)


async def tl_read(driver, addr):
    if hasattr(driver, "read"):
        return await driver.read(addr)
    if hasattr(driver, "get"):
        return await driver.get(addr)
    raise AttributeError("TlUlDriver does not expose a supported read method")


async def tl_write(driver, addr, data, mask=None):
    if hasattr(driver, "write"):
        if mask is None:
            return await driver.write(addr, data)
        return await driver.write(addr, data, mask)
    if hasattr(driver, "put"):
        if mask is None:
            return await driver.put(addr, data)
        return await driver.put(addr, data, mask)
    raise AttributeError("TlUlDriver does not expose a supported write method")


@cocotb.test()
async def test_repair_iteration_2_1(dut):
    random.seed(0xC0C0B0B)
    cov = FunctionalCoverage()

    if not hasattr(dut, "clk_i"):
        raise AttributeError("Expected clk_i clock signal")
    if not hasattr(dut, "rst_ni"):
        raise AttributeError("Expected rst_ni reset signal")

    cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())

    await reset_dut(dut, cycles=8)
    cov.hit("reset_deasserted")

    driver = TlUlDriver(dut, "tl_ul")
    if hasattr(driver, "start"):
        maybe = driver.start()
        if maybe is not None:
            try:
                await maybe
            except TypeError:
                pass

    base_addr = 0
    test_addrs = [0x0, 0x4, 0x8, 0xC, 0x10, 0x14, 0x18, 0x1C]

    cov.hit("tl_driver_initialized")

    for i, addr in enumerate(test_addrs):
        data = (0xA5A50000 ^ (i * 0x11111111)) & 0xFFFFFFFF
        await tl_write(driver, base_addr + addr, data)
        cov.hit("write_smoke")

    for i, addr in enumerate(test_addrs):
        _ = await tl_read(driver, base_addr + addr)
        cov.hit("read_smoke")

    await reset_dut(dut, cycles=3)
    cov.hit("mid_test_reset")

    for i in range(4):
        addr = base_addr + ((i * 4) & 0x3F)
        data = random.getrandbits(32)
        await tl_write(driver, addr, data)
        cov.hit("post_reset_write")

    for i in range(4):
        addr = base_addr + ((i * 4) & 0x3F)
        _ = await tl_read(driver, addr)
        cov.hit("post_reset_read")

    await wait_cycles(dut.clk_i, 10)
    cov.hit("idle_wait")

    cov_path = os.getenv("AUTOVERIFIER_FUNC_COV_FILE", "")
    if cov_path:
        cov.write_json(cov_path)
