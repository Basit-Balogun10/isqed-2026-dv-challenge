import os
import json
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly

from testbench.agents.tlul_driver import TlUlDriver


SEED = 0xC0C0B0B1
random.seed(SEED)


class FuncCov:
    def __init__(self):
        self.bins = {}

    def hit(self, name):
        self.bins[name] = self.bins.get(name, 0) + 1

    def write(self):
        path = os.getenv("AUTOVERIFIER_FUNC_COV_FILE", "").strip()
        if not path:
            return
        data = {
            "schema": "autoverifier_func_cov_v1",
            "seed": SEED,
            "bins": [{"name": k, "hits": v} for k, v in sorted(self.bins.items())],
        }
        Path(path).write_text(json.dumps(data, indent=2, sort_keys=True))


async def tl_write(drv, addr, data, mask=0xF):
    await drv.write(addr, data, mask)


async def tl_read(drv, addr):
    return await drv.read(addr)


async def wait_cycles(clk, n):
    for _ in range(n):
        await RisingEdge(clk)


@cocotb.test()
async def test_repair_iteration_2_1(dut):
    cov = FuncCov()

    clk = dut.clk_i
    rst_n = dut.rst_ni

    cocotb.start_soon(Clock(clk, 10, units="ns").start())

    dut.a_valid_i.value = 0
    dut.a_opcode_i.value = 0
    dut.a_param_i.value = 0
    dut.a_size_i.value = 0
    dut.a_source_i.value = 0
    dut.a_address_i.value = 0
    dut.a_mask_i.value = 0
    dut.a_data_i.value = 0
    dut.a_user_i.value = 0
    dut.d_ready_i.value = 1

    await wait_cycles(clk, 5)
    rst_n.value = 0
    await wait_cycles(clk, 5)
    rst_n.value = 1
    await wait_cycles(clk, 5)

    tl = TlUlDriver(dut, "tl", clk, rst_n)
    if hasattr(tl, "set_idle"):
        tl.set_idle()

    cov.hit("reset_released")

    base_addr = 0x0
    stride = 4

    for i in range(8):
        addr = base_addr + i * stride
        data = (0x11111111 * (i + 1)) & 0xFFFFFFFF
        cov.hit("write_burst")
        await tl_write(tl, addr, data, 0xF)
        await wait_cycles(clk, 1)

    for i in range(8):
        addr = base_addr + i * stride
        cov.hit("read_burst")
        _ = await tl_read(tl, addr)
        await wait_cycles(clk, 1)

    for i in range(4):
        addr = base_addr + (i % 2) * stride
        data = random.getrandbits(32)
        mask = 0xF if (i % 2 == 0) else 0x3
        cov.hit("mixed_mask_access")
        await tl_write(tl, addr, data, mask)
        _ = await tl_read(tl, addr)
        await wait_cycles(clk, 1)

    cov.hit("boundary_probe")
    for offset in [0, 4, 28, 32, 36]:
        addr = base_addr + offset
        await tl_write(tl, addr, random.getrandbits(32), 0xF)
        _ = await tl_read(tl, addr)
        await wait_cycles(clk, 1)

    if hasattr(tl, "idle"):
        await tl.idle()
    else:
        await wait_cycles(clk, 5)

    cov.write()
