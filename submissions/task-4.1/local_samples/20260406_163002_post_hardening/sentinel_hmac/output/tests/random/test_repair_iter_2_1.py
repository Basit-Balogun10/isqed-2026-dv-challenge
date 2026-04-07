import os
import json
import random
from pathlib import Path

import cocotb
from cocotb.triggers import RisingEdge, Timer, ReadOnly
from cocotb.clock import Clock

from testbench.agents import TlUlDriver


DETERMINISTIC_SEED = 0xC0C0B0B1
random.seed(DETERMINISTIC_SEED)


class FunctionalCoverage:
    def __init__(self):
        self.bins = {}
        self.total = 0

    def add_bin(self, name):
        if name not in self.bins:
            self.bins[name] = 0
            self.total += 1

    def hit(self, name):
        self.add_bin(name)
        self.bins[name] += 1

    def to_json(self):
        return {
            "seed": DETERMINISTIC_SEED,
            "bins": self.bins,
            "total_bins": self.total,
            "hit_bins": sum(1 for v in self.bins.values() if v > 0),
        }

    def write(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=2, sort_keys=True)


async def _wait_cycles(clk, n):
    for _ in range(n):
        await RisingEdge(clk)


async def _reset_dut(dut):
    dut.rst_ni.value = 0
    await _wait_cycles(dut.clk_i, 5)
    dut.rst_ni.value = 1
    await _wait_cycles(dut.clk_i, 5)


async def _tl_write(driver, addr, data, mask=0xF):
    await driver.write(addr, data, mask)


async def _tl_read(driver, addr):
    return await driver.read(addr)


async def _safe_getattr(obj, names, default=None):
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


@cocotb.test()
async def test_repair_iteration_2_1(dut):
    clk = dut.clk_i
    cocotb.start_soon(Clock(clk, 10, units="ns").start())

    cov = FunctionalCoverage()
    cov.add_bin("reset_seen")
    cov.add_bin("cmd_sequence")
    cov.add_bin("fifo_activity")
    cov.add_bin("status_poll")
    cov.add_bin("double_pass_attempt")
    cov.add_bin("final_readback")

    await _reset_dut(dut)
    cov.hit("reset_seen")

    driver = TlUlDriver(dut, "clk_i", "rst_ni")
    if hasattr(driver, "start"):
        maybe = driver.start()
        if maybe is not None:
            try:
                await maybe
            except TypeError:
                pass

    base = 0
    regs = {
        "cmd": base + 0x00,
        "status": base + 0x04,
        "key": base + 0x08,
        "msg": base + 0x0C,
        "digest": base + 0x10,
    }

    status_before = await _tl_read(driver, regs["status"])
    cov.hit("status_poll")

    msg_words = [random.getrandbits(32) for _ in range(6)]
    key_words = [random.getrandbits(32) for _ in range(8)]

    for w in key_words:
        await _tl_write(driver, regs["key"], w)
        cov.hit("fifo_activity")

    for w in msg_words[:3]:
        await _tl_write(driver, regs["msg"], w)
        cov.hit("fifo_activity")

    await _tl_write(driver, regs["cmd"], 0x1)
    cov.hit("cmd_sequence")
    await _wait_cycles(clk, 2)

    for w in msg_words[3:]:
        await _tl_write(driver, regs["msg"], w)
        cov.hit("fifo_activity")

    await _tl_write(driver, regs["cmd"], 0x2)
    cov.hit("cmd_sequence")
    await _wait_cycles(clk, 2)

    await _tl_write(driver, regs["cmd"], 0x4)
    cov.hit("cmd_sequence")
    await _wait_cycles(clk, 2)

    cov.hit("double_pass_attempt")
    await _tl_write(driver, regs["cmd"], 0x1)
    await _wait_cycles(clk, 1)
    await _tl_write(driver, regs["cmd"], 0x2)
    await _wait_cycles(clk, 1)
    await _tl_write(driver, regs["cmd"], 0x4)
    await _wait_cycles(clk, 4)

    for _ in range(8):
        _ = await _tl_read(driver, regs["status"])
        cov.hit("status_poll")
        await _wait_cycles(clk, 1)

    digest_reads = []
    for i in range(8):
        val = await _tl_read(driver, regs["digest"] + 4 * i)
        digest_reads.append(val)
        cov.hit("final_readback")

    _ = status_before
    _ = digest_reads

    func_cov_file = os.environ.get("AUTOVERIFIER_FUNC_COV_FILE", "")
    if func_cov_file:
        cov.write(func_cov_file)

    await _wait_cycles(clk, 5)
