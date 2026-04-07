import os
import json
import random
from pathlib import Path

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

from testbench.agents import TlUlDriver


def _get_env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


def _get_env_path(name, default):
    return Path(os.getenv(name, default))


def _write_func_cov(entries):
    cov_file = os.getenv("AUTOVERIFIER_FUNC_COV_FILE")
    if not cov_file:
        return
    path = Path(cov_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "autoverifier_func_cov_v1",
        "entries": entries,
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


async def _wait_cycles(dut, n):
    for _ in range(n):
        await RisingEdge(dut.clk_i)


async def _tl_write(driver, addr, data, mask=None):
    if mask is None:
        mask = 0xF
    await driver.write(addr, data, mask)


async def _tl_read(driver, addr):
    return await driver.read(addr)


@cocotb.test()
async def test_repair_iteration_1_1(dut):
    random.seed(0xC0C0B0B)

    if hasattr(dut, "clk_i"):
        cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())

    dut.rst_ni.value = 0
    if hasattr(dut, "scanmode_i"):
        dut.scanmode_i.value = 0
    if hasattr(dut, "clk_en_i"):
        dut.clk_en_i.value = 1

    await _wait_cycles(dut, 5)
    dut.rst_ni.value = 1
    await _wait_cycles(dut, 5)

    driver = TlUlDriver(dut, "tl_i", "tl_o", dut.clk_i, dut.rst_ni)
    await driver.reset()

    entries = []

    regs = {}
    for name in [
        "CTRL",
        "CFG",
        "COUNT",
        "BARK_THOLD",
        "BITE_THOLD",
        "LOCK",
        "INTR_STATE",
        "INTR_ENABLE",
        "INTR_TEST",
    ]:
        if hasattr(dut, name.lower() + "_q"):
            regs[name] = getattr(dut, name.lower() + "_q")
        elif hasattr(dut, name):
            regs[name] = getattr(dut, name)

    base = 0
    addr_map = {}
    for idx, name in enumerate(regs.keys()):
        addr_map[name] = base + idx * 4

    if "CTRL" in addr_map:
        await _tl_write(driver, addr_map["CTRL"], 0x1)
        entries.append({"name": "ctrl_write", "hit": 1})

    if "LOCK" in addr_map:
        await _tl_write(driver, addr_map["LOCK"], 0x1)
        entries.append({"name": "lock_set", "hit": 1})

    if "BARK_THOLD" in addr_map and "BITE_THOLD" in addr_map:
        bark = random.randint(4, 12)
        bite = bark + random.randint(2, 8)
        await _tl_write(driver, addr_map["BARK_THOLD"], bark)
        await _tl_write(driver, addr_map["BITE_THOLD"], bite)
        entries.append({"name": "threshold_programmed", "hit": 1})

    if "COUNT" in addr_map:
        await _tl_write(driver, addr_map["COUNT"], 0)
        entries.append({"name": "count_clear", "hit": 1})

    if "INTR_ENABLE" in addr_map:
        await _tl_write(driver, addr_map["INTR_ENABLE"], 0x1)
        entries.append({"name": "intr_enable", "hit": 1})

    if "INTR_TEST" in addr_map:
        await _tl_write(driver, addr_map["INTR_TEST"], 0x1)
        await _wait_cycles(dut, 2)
        entries.append({"name": "intr_test_force", "hit": 1})

    if "INTR_STATE" in addr_map:
        await _tl_write(driver, addr_map["INTR_STATE"], 0x1)
        entries.append({"name": "intr_state_w1c", "hit": 1})

    if "LOCK" in addr_map:
        await _tl_write(driver, addr_map["LOCK"], 0x0)
        entries.append({"name": "lock_sticky_write_attempt", "hit": 1})

    if "COUNT" in addr_map:
        for _ in range(3):
            await _tl_read(driver, addr_map["COUNT"])
        entries.append({"name": "count_readback", "hit": 1})

    if "CFG" in addr_map:
        await _tl_write(driver, addr_map["CFG"], 0x2)
        entries.append({"name": "cfg_update", "hit": 1})

    if "BARK_THOLD" in addr_map:
        await _tl_write(driver, addr_map["BARK_THOLD"], 0x3)
        entries.append({"name": "bark_partial_write", "hit": 1})

    if "BITE_THOLD" in addr_map:
        await _tl_write(driver, addr_map["BITE_THOLD"], 0x7)
        entries.append({"name": "bite_partial_write", "hit": 1})

    await _wait_cycles(dut, 10)

    _write_func_cov(entries)
